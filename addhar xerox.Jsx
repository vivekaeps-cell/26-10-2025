// Aadhaar Print Script - Centered Block with Gap & Auto Feedback
var dpi = 300;

// Enlarged card size
var idWidthMM = 95;
var idHeightMM = 60;

// A4 page size
var a4WidthMM = 210;
var a4HeightMM = 297;
var gapMM = 8;

// Convert mm to px
function mmToPx(mm) { return Math.round((mm / 25.4) * dpi); }

// Ensure at least 2 docs are open
if (app.documents.length < 2) {
    alert("Please drag & drop BOTH front and back Aadhaar images into Photoshop before running.");
    exit();
}

// Find newest 2 docs (drag & drop safe)
var allDocs = [];
for (var i = 0; i < app.documents.length; i++) allDocs.push(app.documents[i]);
allDocs.sort(function(a, b) {
    try { return b.fullName.modified - a.fullName.modified; }
    catch (e) { return 0; }
});
var frontDoc = allDocs[0];
var backDoc = allDocs[1];

// Create new A4 grayscale doc
var a4Doc = app.documents.add(mmToPx(a4WidthMM), mmToPx(a4HeightMM), dpi, "Aadhaar_Print", NewDocumentMode.GRAYSCALE, DocumentFill.WHITE);

// Calculate centered positions
var blockWidthMM = idWidthMM + gapMM + idWidthMM;
var leftMarginMM = (a4WidthMM - blockWidthMM) / 2;
var topMarginMM = 10;

// Function to place & close an image
function placeImage(doc, xMM, yMM) {
    app.activeDocument = doc;
    doc.changeMode(ChangeMode.GRAYSCALE);
    doc.resizeImage(UnitValue(idWidthMM, "mm"), UnitValue(idHeightMM, "mm"), dpi, ResampleMethod.BICUBIC);
    doc.selection.selectAll();
    doc.selection.copy();
    doc.close(SaveOptions.DONOTSAVECHANGES);
    app.activeDocument = a4Doc;
    var layer = a4Doc.paste();
    layer.translate(-layer.bounds[0], -layer.bounds[1]);
    layer.translate(mmToPx(xMM), mmToPx(yMM));
}

// Place front & back centered
placeImage(frontDoc, leftMarginMM, topMarginMM);
placeImage(backDoc, leftMarginMM + idWidthMM + gapMM, topMarginMM);

// Auto feedback on canvas (temporary text layer)
var textLayer = a4Doc.artLayers.add();
textLayer.kind = LayerKind.TEXT;
textLayer.textItem.contents = "✅ Aadhaar layout ready";
textLayer.textItem.position = [mmToPx(20), mmToPx(a4HeightMM - 20)];
textLayer.textItem.size = 18;
textLayer.opacity = 80;

// Remove feedback layer after short pause
$.sleep(1500);
textLayer.remove();
