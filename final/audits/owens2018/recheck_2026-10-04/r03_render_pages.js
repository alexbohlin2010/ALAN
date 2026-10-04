// r03: render pages to PNG. Usage: osascript -l JavaScript r03_render_pages.js <pdf> <outdir> <pages comma-sep, 1-based>
ObjC.import('PDFKit'); ObjC.import('AppKit'); ObjC.import('Foundation');
function run(argv) {
  var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  var pgs = argv[2].split(',').map(Number);
  pgs.forEach(function(p){
    var page = doc.pageAtIndex(p-1);
    var b = page.boundsForBox(0);
    var sc = 2.5, w = b.size.width*sc, h = b.size.height*sc;
    var img = $.NSImage.alloc.initWithSize($.NSMakeSize(w,h));
    img.lockFocus;
    $.NSColor.whiteColor.set;
    $.NSBezierPath.fillRect($.NSMakeRect(0,0,w,h));
    var ctx = $.NSGraphicsContext.currentContext.CGContext;
    $.CGContextScaleCTM(ctx, sc, sc);
    page.drawWithBoxToContext(0, ctx);
    img.unlockFocus;
    var tiff = img.TIFFRepresentation;
    var rep = $.NSBitmapImageRep.imageRepWithData(tiff);
    var png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $());
    png.writeToFileAtomically(argv[1] + '/r03_page' + p + '.png', true);
  });
  return 'ok';
}
