// a03: render PDF pages to PNG with PDFKit. Usage: osascript -l JavaScript a03_render_pages.js <pdf> <outdir> <page,page,...>
ObjC.import('PDFKit'); ObjC.import('Foundation'); ObjC.import('AppKit');
function run(argv) {
  var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  var pages = argv[2].split(',').map(Number);
  pages.forEach(function (p) {
    var pg = doc.pageAtIndex(p - 1);
    var img = pg.thumbnailOfSizeForBox($.NSMakeSize(1600, 2070), 1);
    var rep = $.NSBitmapImageRep.imageRepWithData(img.TIFFRepresentation);
    var png = rep.representationUsingTypeProperties(4, $());
    png.writeToFileAtomically(argv[1] + '/a03_page' + p + '.png', true);
  });
  return 'ok';
}
