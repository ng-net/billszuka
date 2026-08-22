
!function(){try{var e="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof globalThis?globalThis:"undefined"!=typeof self?self:{},n=(new e.Error).stack;n&&(e._srcMapDebugIds=e._srcMapDebugIds||{},e._srcMapDebugIds[n]="78a03eaa-86ae-5d6f-8d5c-b03047810ac6")}catch(e){}}();
function post(t){if(t.source===parent&&t.origin===location.protocol+"//"+location.hostname&&"string"==typeof t.data){var o=t.data.indexOf(":"),a=t.data.substr(0,o),n=t.data.substr(o+1);"ddg"===a&&(parent.window.location.href=n)}}window.addEventListener&&window.addEventListener("message",post,!1);
//# debugId=78a03eaa-86ae-5d6f-8d5c-b03047810ac6
