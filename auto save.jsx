// Define Save Folder
var saveFolder = new Folder("C:/Users/vivek/Documents/Photoshop_2025/print/");
if (!saveFolder.exists) { saveFolder.create(); } // Create folder if it doesn’t exist

// Generate Random File Name (Date + Random Number)
var date = new Date();
var randomNum = Math.floor(Math.random() * 10000);
var fileName = "Print_" + date.getTime() + "_" + randomNum + ".jpg";

var saveFile = new File(saveFolder + "/" + fileName);

// Save File as JPG
var jpgOptions = new JPEGSaveOptions();
jpgOptions.quality = 12; // High Quality
jpgOptions.formatOptions = FormatOptions.STANDARDBASELINE;

app.activeDocument.saveAs(saveFile, jpgOptions, true);

// Delete Old Files (Older than 1 Day)
var files = saveFolder.getFiles();
for (var i = 0; i < files.length; i++) {
    var file = files[i];

    if (file instanceof File) {
        var lastModified = file.modified;
        var now = new Date();
        var timeDiff = now.getTime() - lastModified.getTime();
        var daysOld = timeDiff / (1000 * 60 * 60 * 24);

        if (daysOld > 1) { // Delete files older than 1 day
            file.remove();
        }
    }
}

