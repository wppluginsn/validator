<?php
/*
Combined Scanner by sohay
- Permission Scanner
- Backdoor/Shell Scanner
Version: 2.0.0
*/
echo '<style>
body {background-color:#000;color:green;} 
body,td,th { font: 9pt Courier New;margin:0;vertical-align:top; } 
span,h1,a { color:#00ff00} 
span { font-weight: bolder; } 
h1 { border:1px solid #00ff00;padding: 2px 5px;font: 14pt Courier New;margin:0px; } 
div.content { padding: 5px;margin-left:5px;} 
a { text-decoration:none; } 
a:hover { background:#ff0000; } 
.ml1 { border:1px solid #444;padding:5px;margin:0;overflow: auto; } 
.bigarea { width:100%;height:450px;font-size:11px; } 
input, textarea, select { margin:0;color:#00ff00;background-color:#000;border:1px solid #00ff00; font: 9pt Monospace,"Courier New"; } 
form { margin:0px; } 
#toolsTbl { text-align:center; } 
.toolsInp { width: 80%; } 
.main th {text-align:left;} 
.main tr:hover{background-color:#5e5e5e;} 
.main td, th{vertical-align:middle;} 
pre {font-family:Courier,Monospace;} 
.style2 {color: #00FF00} 
.style3 {color: #009900} 
.style4 {color: #006600} 
.style5 {color: #00CC00} 
.style6 {color: #003300} 
.style8 {color: #33CC00}
table { width: 100%; border-collapse: collapse; }
table td { padding: 5px; border-bottom: 1px solid #333; }
.tab-container { margin: 20px 0; }
.tab-button { padding: 10px 20px; margin-right: 5px; cursor: pointer; background: #003300; border: 1px solid #00ff00; color: #00ff00; }
.tab-button.active { background: #00ff00; color: #000; font-weight: bold; }
.tab-content { display: none; padding: 20px; border: 1px solid #00ff00; margin-top: 10px; }
.tab-content.active { display: block; }
</style>';

set_time_limit(0);
error_reporting(0);
@ini_set('zlib.output_compression', 0);
@ini_set('implicit_flush', 1);
for($i = 0; $i < ob_get_level(); $i++) { ob_end_flush(); }
ob_implicit_flush(1);

$path = getcwd();
if(isset($_GET['dir'])){
    $path = $_GET['dir'];
}

// Self delete
if(isset($_GET['kill'])){
    unlink(__FILE__);
    exit;
}

echo "<h1>🔍 Combined Security Scanner</h1>";
echo "<a href='?kill'><font color='red'>[Self Delete]</font></a> | ";
echo "<a href='?'><font color='yellow'>[Refresh]</font></a><br><br>";
echo '<form action="" method="get">
    <input type="text" name="dir" value="'.$path.'" style="width: 700px;">
    <input type="submit" value="🔎 Scan Directory">
</form><br>';
echo "CURRENT DIR: <font color='yellow'>$path</font><br><br>";

// Tab Navigation
echo '<div class="tab-container">
    <button class="tab-button active" onclick="showTab('permission')">📁 Permission Scanner</button>
    <button class="tab-button" onclick="showTab('backdoor')">🐚 Backdoor Scanner</button>
</div>';

// Permission Scanner Tab
echo '<div id="permission" class="tab-content active">';
echo "<h2>📁 Directory Permission Scanner</h2>";
scanPermissions($path);
echo '</div>';

// Backdoor Scanner Tab
echo '<div id="backdoor" class="tab-content">';
echo "<h2>🐚 Backdoor/Shell Scanner</h2>";

// Delete file functionality
if(isset($_GET['delete'])){
    unlink($_GET['delete']);
    $status = "<font color='red'>FAILED</font>";
    if(!file_exists($_GET['delete'])){
        $status = "<font color='yellow'>Success</font>";
    }
    echo "TRY TO DELETE: ".
    $_GET['delete']." $status <br><br>";
}

scanBackdoor($path);
echo '</div>';

// JavaScript for tabs
echo '<script>
function showTab(tabName) {
    var tabs = document.getElementsByClassName("tab-content");
    var buttons = document.getElementsByClassName("tab-button");
    
    for(var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove("active");
    }
    for(var i = 0; i < buttons.length; i++) {
        buttons[i].classList.remove("active");
    }
    
    document.getElementById(tabName).classList.add("active");
    event.target.classList.add("active");
}
</script>';

// ============ PERMISSION SCANNER FUNCTIONS ============
function scanPermissions($dir) {
    if(!is_readable($dir)) {
        echo "<font color='red'>Cannot read directory: $dir</font><br>";
        return;
    }
    
    $files = scandir($dir);
    echo "<table class='main'>";
    echo "<tr><th>Type</th><th>Name</th><th>Permission</th><th>Status</th></tr>";
    
    foreach($files as $file) {
        if($file === "." || $file === "..") continue;
        
        $fullPath = $dir . '/' . $file;
        $perms = fileperms($fullPath);
        $permsOctal = substr(sprintf('%o', $perms), -4);
        
        $type = is_dir($fullPath) ? "📁 DIR" : "📄 FILE";
        $status = "";
        $color = "green";
        
        // Check for dangerous permissions
        if(is_writable($fullPath)) {
            $status = "⚠️ WRITABLE";
            $color = "yellow";
        }
        if($permsOctal == "0777") {
            $status = "🔴 DANGEROUS (777)";
            $color = "red";
        }
        if(is_dir($fullPath) && is_writable($fullPath)) {
            $status = "⚠️ WRITABLE DIRECTORY";
            $color = "orange";
        }
        
echo "<tr>";
        echo "<td>$type</td>";
        echo "<td><a href='?dir=$fullPath'>".htmlspecialchars($file)."</a></td>";
        echo "<td><font color='$color'>$permsOctal</font></td>";
        echo "<td><font color='$color'>$status</font></td>";
        echo "</tr>";
    }
    echo "</table>";
}

// ============ BACKDOOR SCANNER FUNCTIONS ============
function save($fname, $value){
    $file = fopen($fname, "a");
    fwrite($file, $value);
    fclose($file);
}

function checkBackdoor($file_location){
    global $path;
    $patern = "#exec\(|gzinflate\(|file_put_contents\(|file_get_contents\(|system\(|passthru\(|shell_exec\(|move_uploaded_file\(|eval\(|base64_decode\(|assert\(|preg_replace.*\/e|create_function\(|include.*\$_|require.*\$_|`.*`|proc_open\(|popen\(#i";
    
    $contents = file_get_contents($file_location);
    if(strlen($contents) > 0){
        if(preg_match($patern, $contents)){
            $filesize = filesize($file_location);
            $filesizeKB = round($filesize / 1024, 2);
            
            echo "<div style='margin:10px 0; padding:10px; border:1px solid red;'>";
            echo "[+] <font color='red'>SUSPICIOUS FILE DETECTED</font><br>";
            echo "📄 File: <font color='yellow'>$file_location</font><br>";
            echo "📊 Size: <font color='yellow'>$filesizeKB KB</font><br>";
            echo "<a href='?delete=$file_location&dir=$path'><font color='red'>[🗑️ DELETE]</font></a> | ";
            echo "<a href='$file_location' target='_blank'><font color='yellow'>[👁️ VIEW]</font></a><br><br>";
            
            save("shell-found.txt", "$file_location\n");
            
            echo '<textarea class="bigarea">'.htmlspecialchars($contents).'</textarea>';
            echo "</div>";
        }
    }   
}

function scanBackdoor($current_dir){
    static $fileCount = 0;
    static $suspectCount = 0;
    
    if(is_readable($current_dir)){
        $dir_location = scandir($current_dir);
        foreach($dir_location as $file) {
            if($file === "." || $file === ".."){
                continue;
            }
            
            $file_location = str_replace("//", "", $current_dir.'/'.$file);
            $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
            
            // Scan PHP files
            if($ext == "php") {
                $fileCount++;
                echo "<font color='#666'>Scanning ($fileCount): $file_location</font><br>";
                flush();
                ob_flush();
                checkBackdoor($file_location);
            } else if(is_dir($file_location)){ 
                // Recursively scan subdirectories
                scanBackdoor($file_location);
            }
        }
    }
    
    if($fileCount > 0 && $suspectCount == 0) {
        echo "<br><font color='green'>✓ Scanned $fileCount PHP files - No threats detected</font><br>";
    }
}