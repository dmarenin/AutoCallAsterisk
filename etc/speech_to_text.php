#!/usr/local/bin/php -q
<?php
$agivars = array();
while (!feof(STDIN)) {
	$agivar = trim(fgets(STDIN));
	if ($agivar === '')
		break;
	$agivar = explode(':', $agivar);
	$agivars[$agivar[0]] = trim($agivar[1]);
}

$filename = $agivars['agi_arg_1'];
$channel = $agivars['agi_channel'];
$callerid = $agivars['agi_callerid'];

//system('/usr/local/bin/sox '.$filename.'.wav -r 16000 -b 16 -c 1 '.$filename.'-pcm.wav');

$cmd = exec('/usr/local/bin/curl --silent -F "Content-Type=audio/x-pcm;bit=16;rate=16000" -F "audio=@'.$filename.'.wav" 192.168.7.220:8090/speech_to_text?channel='.$channel.'&callerid='.$callerid, $res);

//$cmd = exec('/usr/local/bin/curl --silent -F "Content-Type=audio/x-pcm;bit=16;rate=16000" -F "audio=@'.$filename.'-pcm.wav" 192.168.7.220:8090/speech_to_text', $res);

$res_str = implode($res);

echo 'SET VARIABLE TEXT_SP_RES "'.(int)$res_str.'"'."\n";

fgets(STDIN);

exit(0);

/* 
echo 'VERBOSE ("'.$voice_text.'")'."\n";
fgets(STDIN);
 */
?>