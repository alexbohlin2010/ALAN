// a01: independent text-layer extraction via PDFKit. Usage: osascript -l JavaScript a01_extract_text.js <pdf> <outdir>
ObjC.import('PDFKit'); ObjC.import('Foundation');
function run(argv) {
  var pdf = argv[0], out = argv[1];
  var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(pdf));
  var n = doc.pageCount;
  var all = '';
  for (var i = 0; i < n; i++) {
    var s = doc.pageAtIndex(i).string.js;
    all += '\n=====PAGE ' + (i+1) + '=====\n' + s;
    $(s).writeToFileAtomicallyEncodingError(out + '/page' + (i+1) + '.txt', true, $.NSUTF8StringEncoding, $());
  }
  $(all).writeToFileAtomicallyEncodingError(out + '/a01_pdftext_all.txt', true, $.NSUTF8StringEncoding, $());
  return 'pages=' + n;
}
