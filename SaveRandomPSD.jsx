// Photoshop Script to Save Document

// Specify the saving location
var savingLocation = "C:/Users/vivek/Documents/Photoshop_2025/Record/";

// Ensure the folder exists (optional, remove if handled separately)
var saveFolder = new Folder(savingLocation);
if (!saveFolder.exists) {
    saveFolder.create();
}

// Function to get the next sequential file number
function getNextSequentialNumber() {
    var files = saveFolder.getFiles("*.psd");
    var maxNumber = 0;
    for (var i = 0; i < files.length; i++) {
        var fileName = files[i].name;
        var match = fileName.match(/^(\d{5})\.psd$/);
        if (match) {
            var number = parseInt(match[1], 10);
            if (number > maxNumber) {
                maxNumber = number;
            }
        }
    }
    var nextNumber = maxNumber + 1;
    var sequentialNumber = "00000" + nextNumber; // Add leading zeros
    return sequentialNumber.slice(-5); // Keep only the last 5 digits
}

// Error handling to check for an active document
if (app.documents.length > 0) {
    var doc = app.activeDocument; // Get active document
    var sequentialNumber = getNextSequentialNumber(); // Generate file number
    var filePath = savingLocation + sequentialNumber + ".psd";
    
    // Save the document as a PSD file
    var psdSaveOptions = new PhotoshopSaveOptions();
    doc.saveAs(new File(filePath), psdSaveOptions, true);
    
    // Confirmation message without OK button
    var feedbackMessage = "Document saved as " + filePath;
    $.writeln(feedbackMessage); // Write to console instead of alert
} else {
    $.writeln("No active document found. Please open a document and try again.");
}
