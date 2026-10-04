// r01: independent PDFKit text per page. Usage: osascript -l JavaScript r01_extract_text.js <pdf> <outdir>
ObjC.import('PDFKit'); ObjC.import('Foundation');
function run(argv) {
  var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  var n = doc.pageCount;
  for (var i = 0; i < n; i++) {
    var s = doc.pageAtIndex(i).string.js;
    $(s).writeToFileAtomicallyEncodingError(argv[1] + '/page' + (i+1) + '.txt', true, $.NSUTF8StringEncoding, $());
  }
  return 'pages=' + n;
}
