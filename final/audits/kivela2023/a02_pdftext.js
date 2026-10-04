ObjC.import('PDFKit');ObjC.import('Foundation');
var p='data/raw/impacts/narrative of fireflies/Kivela_Elgert_Lehtonen_Candolin_2023_STOTEN_glowworm.pdf';
var d=$.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath($.NSFileManager.defaultManager.currentDirectoryPath.js+'/'+p));
var n=d.pageCount; var out='';
for(var i=0;i<n;i++){out+='\n=====PAGE '+(i+1)+'=====\n'+d.pageAtIndex(i).string.js;}
$.NSString.alloc.initWithUTF8String(out).writeToFileAtomicallyEncodingError($.NSString.stringWithString(ObjC.unwrap($.NSProcessInfo.processInfo.environment.objectForKey('OUT'))),true,4,$());
