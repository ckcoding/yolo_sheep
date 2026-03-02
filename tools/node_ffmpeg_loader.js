
console.error("DEBUG: Starting node_ffmpeg_loader.js");
const fs = require('fs');

// Prevent unexpected exits
const realExit = process.exit;
process.exit = function (code) {
    console.error(`DEBUG: Process.exit called with code ${code}`);
    // throw new Error("Process.exit called"); // Optional: throw to see stack trace
};

// Mock Browser Environment deeply
global.window = global;
global.self = global;
global.location = {
    href: 'https://my.jia.360.cn/resource/js/common/libffmpeg.js',
    protocol: 'https:',
    host: 'my.jia.360.cn',
    pathname: '/resource/js/common/libffmpeg.js',
    search: '',
    hash: ''
};
global.document = {
    createElement: function () { return {}; },
    currentScript: { src: 'https://my.jia.360.cn/resource/js/common/libffmpeg.js' }
};

// Emscripten specific overrides
// Emscripten specific overrides
var Module = global.Module || {};
Object.assign(Module, {
    onRuntimeInitialized: function () {
        console.error("FFmpeg Core Initialized!");
        // Notify usage ready
        if (global.onReady) global.onReady();
    },
    print: function (text) { console.error("[FFMPEG-LOG]", text); },
    printErr: function (text) { console.error("[FFMPEG-ERR]", text); },
    locateFile: function (path, prefix) {
        console.error(`[FFMPEG] locateFile requested: ${path}`);
        return path;
    },
    // Sometimes helpful for debugging startup
    postRun: [function () { console.error("[FFMPEG] postRun"); }],
    preRun: [function () { console.error("[FFMPEG] preRun"); }]
});
// Synchronize with global for test_decoder.js access
global.Module = Module;

// Load the library
const libCode = fs.readFileSync('tools/libffmpeg.js', 'utf8');
console.error(`DEBUG: Read libffmpeg.js, size: ${libCode.length} bytes`);

try {
    // Attempting to eval
    console.error("DEBUG: Executing eval...");

    // We already defined 'Module' in this scope.
    // 'var Module' inside libCode should attach to it.
    eval(libCode);

    console.error("DEBUG: Eval finished.");
} catch (e) {
    console.error("Eval Error:", e);
}

module.exports = Module;
