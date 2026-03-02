#!/usr/bin/env node
/**
 * 360 Camera Live Stream Decoder (Optimized)
 * Decodes encrypted HEVC stream and outputs raw YUV420P to stdout
 * 
 * Optimizations:
 * - Reduced initial buffer to 128KB for faster startup
 * - Parallel stream connection during WASM init
 * - Smaller decode batches for smoother playback
 * 
 * Usage: node decoder_service.js | ffplay -f rawvideo -pixel_format yuv420p -video_size 1920x1080 -
 */

const https = require('https');

// ============ 配置 ============
const STREAM_URL = process.env.STREAM_URL || "https://flv-live.jia.360.cn/live_jia_personal/_LC_RE_non_36017050007113417689326961801925_CX.flv";
const PLAY_KEY = process.env.PLAY_KEY || "b8626411e2b666c44486d7081a2c04d71ebc0b5ad0be4b18aa042b94767cfd53";

// 优化参数
const INITIAL_BUFFER_SIZE = 128 * 1024; // 128KB (原 512KB) - 更快启动
const CHUNK_SIZE = 64 * 1024; // 64KB 数据块
const MAX_CONNECT_RETRIES = 5;
const RETRY_BASE_DELAY_MS = 1500;

// ============ 预连接流 (在 WASM 加载时并行) ============
let streamBuffer = Buffer.alloc(0);
let streamReady = false;
let streamResponse = null;
let connectAttempts = 0;

function printConnectionHint(err, statusCode) {
    if (statusCode === 401 || statusCode === 403) {
        console.error("[Service] Hint: stream auth failed. STREAM_URL or PLAY_KEY may be expired.");
        return;
    }
    if (err && (err.code === 'ECONNRESET' || err.message === 'socket hang up')) {
        console.error("[Service] Hint: connection was reset by server. This often means expired STREAM_URL/PLAY_KEY.");
        return;
    }
    if (err && err.code === 'ENOTFOUND') {
        console.error("[Service] Hint: DNS lookup failed. Check network/DNS, then retry.");
        return;
    }
    if (err && err.code === 'ETIMEDOUT') {
        console.error("[Service] Hint: connection timed out. Check network quality or retry later.");
    }
}

function connectStream() {
    connectAttempts++;
    console.error(`[Service] Connecting to stream (attempt ${connectAttempts}/${MAX_CONNECT_RETRIES})...`);

    const req = https.get(STREAM_URL, { timeout: 10000 }, (response) => {
        if (response.statusCode !== 200) {
            console.error("[Service] HTTP Error:", response.statusCode);
            printConnectionHint(null, response.statusCode);

            response.resume(); // drain socket
            if (connectAttempts < MAX_CONNECT_RETRIES) {
                const delay = RETRY_BASE_DELAY_MS * connectAttempts;
                console.error(`[Service] Retrying in ${delay}ms...`);
                setTimeout(connectStream, delay);
                return;
            }
            process.exit(1);
        }

        streamResponse = response;
        console.error("[Service] Stream connected!");

        response.on('data', (chunk) => {
            streamBuffer = Buffer.concat([streamBuffer, chunk]);
            if (!streamReady && streamBuffer.length >= INITIAL_BUFFER_SIZE) {
                streamReady = true;
                console.error(`[Service] Buffer ready: ${streamBuffer.length} bytes`);
            }
        });

        response.on('error', (err) => {
            console.error("[Service] Stream error:", err);
            printConnectionHint(err);
            process.exit(1);
        });
    });

    req.on('timeout', () => req.destroy(Object.assign(new Error('request timeout'), { code: 'ETIMEDOUT' })));
    req.on('error', (err) => {
        console.error("[Service] Request error:", err);
        printConnectionHint(err);

        if (connectAttempts < MAX_CONNECT_RETRIES) {
            const delay = RETRY_BASE_DELAY_MS * connectAttempts;
            console.error(`[Service] Retrying in ${delay}ms...`);
            setTimeout(connectStream, delay);
            return;
        }

        console.error("[Service] Max retries reached. Please refresh STREAM_URL and PLAY_KEY from 360 API.");
        process.exit(1);
    });
}

console.error("[Service] Pre-connecting to stream...");
connectStream();

// ============ Emscripten Module ============
var Module = {
    onRuntimeInitialized: function () {
        console.error("[Service] FFmpeg Core Initialized!");
        if (global.onReady) global.onReady();
    },
    print: function (text) { /* silent */ },
    printErr: function (text) { /* silent - reduce log overhead */ },
    locateFile: function (path) { return path; }
};
global.Module = Module;

// Load libffmpeg.js (parallel with stream connection)
console.error("[Service] Loading WASM decoder...");
require('./node_ffmpeg_loader.js');

let frameCount = 0;
let isOpened = false;
let bufPtr = null;
let infoPtr = null;

global.onReady = function () {
    console.error("[Service] Decoder Ready!");

    try {
        // Video callback - output YUV to stdout
        const videoCallbackPtr = Module.addFunction(function (yPtr, size, pts, width, height) {
            frameCount++;

            if (frameCount === 1) {
                console.error(`[Service] First frame: ${width}x${height}`);
            }

            // 直接输出 YUV 数据
            try {
                process.stdout.write(Buffer.from(Module.HEAPU8.buffer, yPtr, size));
            } catch (e) { }

            if (frameCount % 100 === 0) {
                console.error(`[Service] Frame ${frameCount}`);
            }
        }, 'viiiii');

        const audioCallbackPtr = Module.addFunction(function () { }, 'viiii');
        const seekCallbackPtr = Module.addFunction(function () { }, 'vi');

        // Init Decoder
        var ret = Module._initDecoder(5242880, 0, 0, 0, 0, 1);
        if (ret !== 0) {
            console.error("[Service] Init failed:", ret);
            process.exit(1);
        }

        // Prepare key
        const keyPtr = Module.allocateUTF8(PLAY_KEY);
        const keyListPtr = Module.allocateUTF8(JSON.stringify([PLAY_KEY]));
        infoPtr = Module._malloc(28);
        bufPtr = Module._malloc(1024 * 1024);

        // 等待流数据就绪
        function waitForStream() {
            if (!streamReady) {
                setTimeout(waitForStream, 50);
                return;
            }

            console.error("[Service] Opening decoder...");

            // 发送初始数据
            Module.HEAPU8.set(streamBuffer, bufPtr);
            Module._sendData(bufPtr, streamBuffer.length);
            streamBuffer = Buffer.alloc(0);

            // 打开解码器
            Module.HEAPU8.fill(0, infoPtr, infoPtr + 28);
            const openRet = Module._openDecoder(infoPtr, 7, videoCallbackPtr, audioCallbackPtr, seekCallbackPtr, keyPtr, 0, 0, keyListPtr);

            if (openRet !== 0) {
                console.error("[Service] Failed to open decoder:", openRet);
                process.exit(1);
            }

            const info = Module.HEAP32.subarray(infoPtr >> 2, (infoPtr >> 2) + 7);
            console.error(`[Service] Video: ${info[2]}x${info[3]} - Starting playback!`);
            isOpened = true;

            // 解码初始帧
            while (Module._decodeOnePacket() === 0) { }

            // 持续处理流数据
            streamResponse.on('data', (chunk) => {
                streamBuffer = Buffer.concat([streamBuffer, chunk]);

                while (streamBuffer.length >= CHUNK_SIZE) {
                    Module.HEAPU8.set(streamBuffer.subarray(0, CHUNK_SIZE), bufPtr);
                    const consumed = Module._sendData(bufPtr, CHUNK_SIZE);
                    if (consumed > 0) {
                        streamBuffer = streamBuffer.subarray(consumed);
                    } else {
                        break;
                    }
                    while (Module._decodeOnePacket() === 0) { }
                }
            });

            streamResponse.on('end', () => {
                console.error(`[Service] Done. Frames: ${frameCount}`);
                process.exit(0);
            });
        }

        waitForStream();

        // Handle signals
        process.on('SIGINT', () => {
            console.error(`\n[Service] Stopped. Frames: ${frameCount}`);
            process.exit(0);
        });

        process.stdout.on('error', (err) => {
            if (err.code === 'EPIPE') process.exit(0);
        });

    } catch (e) {
        console.error("[Service] Error:", e);
        process.exit(1);
    }
};
