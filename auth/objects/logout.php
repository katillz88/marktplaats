<?php
//include_once('../../include/config.php');
include ("../../include/inc_config_general.php");

if(!isset($_SESSION)){
	session_start();
}
foreach($_SESSION as $key) {
	unset($_SESSION[$key]);
}
#unset($_SESSION['login']);
#unset($_SESSION['password']);
session_destroy();
$sessionPath = session_get_cookie_params();
setcookie(session_name(), "", 0, $sessionPath["path"], $sessionPath["domain"]);
unset($login, $password, $entered_login, $entered_password);

$url="Location: ". $ScriptRoot ."admin/";
header($url);
?>
