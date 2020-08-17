<?php
//*********************************************************************
// Marktplaats Checker (c) 2006-2013 Matthijs Draijer
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; version 2 of the License.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
//*********************************************************************

include ("../general_include/general_config.php");
include ("../general_include/shared_functions.php");
include ("../general_include/class.phpmailer.php");

include ("include/inc_config_general.php");
include ("lng/language_$Language.php");
include ("include/inc_functions.php");
$publicPage = true;
include ("include/inc_head.php");

setlocale(LC_ALL, 'nl_NL');

if(isset($_REQUEST['forcedID'])) {
 $Termen  = array($_REQUEST['forcedID']);
 $Checken = true;
} else {
 $Termen  = getZoekTermen('', date("w"), date("H"), 1);
}

$debug = 0;

if($Checken) { 
	foreach($Termen as $term) {
		# Alle advertenties inactief zetten.
		# Advertenties die in deze run gevonden worden, worden weer actief gezet
		makeAdsInactive($term);
		
		# Initialiseren van verschillende variabelen
		$teller_n = $teller_c = $teller_b = 0;
		$PlainMessage = $PlainItem = $HTMLItem = $HTMLMessage = $Subjects = $foundIDs = array();
		$p = 1;
		$reclame = '';
		$extraWitregel = false;
		$nextPage    = true;
		
		# Zoek data van de huidige zoekopdracht op
		$ZoekData = getZoekData($term);					
		$UserData = getUserData($ZoekData['user']);
		$rss   = $UserData['RSS'];  
		$URL    = $ZoekData['URL'];
		if($URL == '') $URL = getURL($term);  
		//$URL = addPCtoURL($URL, $UserData['postcode']);
		//$URL = addLimit2URL($URL, 100);
		//$URL .= $URL."&sortBy=SortIndex";
		
		# Als er een mail verstuurd moet worden, mail initialiseren
		if($rss == 0 OR $rss == 2) {
			$PlainHeader = "";
   
   		$HTMLHeader  = "<!--     Deze pagina is onderdeel van $ScriptTitle $Version gemaakt door Matthijs Draijer     -->\n\n";
   		$HTMLHeader .= "<html>\n";
   		$HTMLHeader .= "<head>\n";
   		$HTMLHeader .= " <link rel='stylesheet' type='text/css' href='$ScriptRoot/include/style_mail.css'>\n";
   		$HTMLHeader .= " <title>$ScriptTitle $Version</title>\n";
   		$HTMLHeader .= "</head>\n";
   		$HTMLHeader .= "<body>\n";
   		$HTMLHeader .= "<center>\n";
   		$HTMLHeader .= "<table width='400px' align='center' border=0>\n";
   	}
   	
   	# Als we reclame hebben, moet dat bovenaan de mail getoond worden
   	if(($rss == 0 OR $rss == 2) AND $reclame != '') {
   		$HTMLItem  = "<tr>\n"; 
   		$HTMLItem .= " <td colspan='2' align='center'>". showBlock($reclame) ."</td>";
   		$HTMLItem .= "</tr>\n";
   		
   		$HTMLHeader  .= $HTMLItem;
   		$PlainHeader .= $reclame;
   		$extraWitregel = true;
   	}
   	
   	# Na reclame moet er wel witregel komen
   	if($extraWitregel) {
   		$HTMLItem  = "<tr>\n"; 
   		$HTMLItem .= " <td colspan='2' align='center'>&nbsp;</td>";
   		$HTMLItem .= "</tr>\n";
   		
   		$HTMLHeader  .= $HTMLItem;
   		$PlainHeader .= "\n\n\n";
   	}
   	
   	# Zolang er nog volgende pagina is moet er door gegaan worden met checken.
   	while($nextPage) {
   		# Initialiseren van de hele bende
   		set_time_limit(30);
   		$newFound = false;
   		$inhoud   = file_get_contents(addPage2URL($URL,$p));
   		$teller_p = 0;
   		   		   
   		# Alleen de relevante advertenties inlezen
   		$string = getString('<script id="__NEXT_DATA__" type="application/json">', '</script>', $inhoud, 0);   
   		$json = json_decode($string[0], true);
   		   		
   		# Array maken met losse advertenties
   		$listings = $json['props']['pageProps']['searchRequestAndResponse']['listings'];
   		
   		$maximum = (count($listings)-1);
   		
   		# Bij debuggen even laten zien welke pagina wordt bekeken
   		if($debug != 0) echo "<h2><a href='". addPage2URL($URL,$p) ."'>pagina $p</a></h2>\n";
   		
   		# Bij ontwikkelen hoeven niet alle advertenties doorlopen te worden.
   		# 15 zijn voldoende
   		if($debug == 2) {
   			echo "URL : $URL<br>\nMaximum : $maximum<br>\n<br>\n";
   			if($maximum > 5) $maximum = 5;
   		}
   		
   		# Doorloop alle advertenties op de pagina
   		for($i=0 ; $i <= $maximum ; $i++) {
   			$opnemenInMail = true;
   			$advertentie = $listings[$i];
   			$marktplaatsID = substr($advertentie['itemId'], 1);
   			
   			# Bij ontwikkelen de ruwe tekst laten zien
    		if($debug == 2) {
    			echo '<hr>';
    			echo '[$i = '. $i .']<br>';
    			echo showArray('', $advertentie).'<br>';
    		} 
    		
    		# Alleen als er een plaatsnaam bekend is moet die geprocesed worden.
    		# Zonder plaatsnaam is het vaak een webshop of andere ongein
    		# Hetzelfde geld voor een advertentie die nog niet gevonden is deze batch
    		if(isset($advertentie['location']['cityName']) AND !in_array($marktplaatsID, $foundIDs)) {
    			$newFound = true;
    			$foundIDs[] = $marktplaatsID;
    			$changedTitle = $changedPrijs = $changedData = $changedTransport = $changedStatus = $newItem = false;
    			$basicData['status'] = $basicData['transport'] = $basicData['picture'] = '';
    			
    			$basicData['key']					= $marktplaatsID;
					$basicData['URL']					=	$advertentie['vipUrl'];
					$basicData['title'] 			= $advertentie['title'];
					$basicData['descr_short']	= $advertentie['description'];
					$basicData['price']				= $advertentie['priceInfo']['priceCents'];
					$basicData['plaats']			= $advertentie['location']['cityName'];
					//$basicData['provincie']	= $advertentie['location']['countryName'];
					$basicData['afstand']			= $advertentie['location']['distanceMeters'];
					
					if(isset($advertentie['attributes'][0]) AND $advertentie['attributes'][0]['key'] == 'condition')	$basicData['status'] = $advertentie['attributes'][0]['value'];
					if(isset($advertentie['attributes'][1]) AND $advertentie['attributes'][1]['key'] == 'condition')	$basicData['status'] = $advertentie['attributes'][1]['value'];
					if(isset($advertentie['attributes'][0]) AND $advertentie['attributes'][0]['key'] == 'delivery')	$basicData['transport'] = $advertentie['attributes'][0]['value'];
					if(isset($advertentie['attributes'][1]) AND $advertentie['attributes'][1]['key'] == 'delivery')	$basicData['transport'] = $advertentie['attributes'][1]['value'];
					if(isset($advertentie['imageUrls']))	$basicData['picture']	 =	implode("|", $advertentie['imageUrls']);
						
					$basicData['URL_short']		=	'https://link.marktplaats.nl/'. $advertentie['itemId'];
					$basicData['price_add']		=	$advertentie['priceInfo']['priceType'];
					$basicData['date']				=	strtotime($advertentie['date']); 
					//$detailData['visits']		=	formatString($bezoeken[0]); 
					$basicData['verkoper']		=	$advertentie['sellerInformation']['sellerName']; 
					$basicData['verkoper_id']	= $advertentie['sellerInformation']['sellerId'];
    			    			
    			# Als hij nog niet bekend is, moet er verder gezocht worden      
    			if(!NewItem($basicData['key'], $term)) {
    				$oldData = getPageDataByMarktplaatsID($basicData['key']);
       
    		   	# Wijziging in titel
       			if(urldecode($oldData['title']) != $basicData['title']) {
       				$changedTitle = true;
       				$changedData = true;
       			}
       
       			# Wijziging in prijs
       			if(formatPrice($oldData['prijs'], false) != formatPrice($basicData['price'], false)) {
       			  $changedPrijs = true;
       			  $changedData = true;
       			}
       			       			
       			# Wijziging in transport
       			if($oldData['transport'] != $basicData['transport']) {
       			  $changedTransport = true;
       			  $changedData = true;
       			}
       			       			
       			# Wijziging in status
       			if($oldData['status'] != $basicData['status']) {
       			  $changedStatus = true;
       			  $changedData = true;
       			}
       		} else {
       			$newItem = true;       			
       		}


					# Doe een 1ste check of deze op basis van prijs moet worden opgenomen in de mail
					if($ZoekData['pmin'] != '' OR $ZoekData['pmax'] != '') {
						$opnemenInMail = false;
						
						# Bij gereserveerd moet er gecheckt worden met de oude prijs
						# niet de huidige, die staat op -1
						if($data['price_add'] == 'RESERVED' AND $changedPrijs) {
							$priceToCheck = $oldData['prijs'];
						} else {
							$priceToCheck = $basicData['price'];
						}
						
						if($ZoekData['pmin'] != '') {
							if($ZoekData['pmax'] != '') {
								if($priceToCheck > (100*$ZoekData['pmin']) AND $priceToCheck < (100*$ZoekData['pmax'])) {
									$opnemenInMail = true;
								}
							} elseif($priceToCheck > (100*$ZoekData['pmin'])) {
								$opnemenInMail = true;
							}
       			}
       			
       			if($ZoekData['pmax'] != '') {
       				if($priceToCheck < (100*$ZoekData['pmin'])) {
       					$opnemenInMail = true;
       				}
       			}
       		}
       		       		       		
       		# Bij een nieuwe of gewijzigde advertenties moet de pagina van de advertentie worden ingelezen
       		if(($newItem OR $changedData) AND $opnemenInMail) {
       			$detailData = getAdvancedMarktplaatsData('https://www.marktplaats.nl'.$basicData['URL']);
       			$data = array_merge($basicData, $detailData);
       			
       			# Staat de coordinaten in de advertentie of moet er even worden gezocht
       			if($detailData['long'] != '' AND $detailData['lat'] != '') {
       				$coord = array($detailData['lat'], $detailData['long']);
						} else {
							$coord = getCoordinates('', '', $data['plaats']);							
						}
																										
						$afstand		= getDistance($UserData['coord'], $coord);
						$data['afstand'] = round($afstand/1000);						
       			
       			# Doe een 2de check of deze op basis van afstand moet worden opgenomen in de mail
       			if($ZoekData['dmin'] != '' OR $ZoekData['dmax'] != '') {
							$opnemenInMail = false;
														
							if($ZoekData['dmin'] != '') {
								if($ZoekData['dmax'] != '') {
									if($afstand > (1000*$ZoekData['dmin']) AND $afstand < (1000*$ZoekData['dmax'])) {
										$opnemenInMail = true;
									}
								} elseif($afstand > (1000*$ZoekData['dmin'])) {
									$opnemenInMail = true;
								}
       				}
       		  	       			  	
       				if($ZoekData['dmax'] != '') {
       					if($afstand < (1000*$ZoekData['dmax'])) {       							
       						$opnemenInMail = true;
       					}
       				}
       			}
       		} else {
       			$data = $basicData;       			
       		}
       		
       		# Bij ontwikkelen de losse data laten zien
       		if($debug == 2) {
       			echo '<hr>';
       			foreach($data as $key => $value) {
       				echo "<b>$key</b> -> $value<br>\n\n";
       			}
       			
       			if($newItem) echo "Nieuw<br>\n";
       			if($changedData) echo "Gewijzigd<br>\n";
       		}
       		       		
       		# Bij een nieuwe of gewijzigde advertentie tekst voor de mail opstellen
       		if(($newItem OR $changedData) AND $opnemenInMail) {
       			if($rss == 0 OR $rss == 2) {
       				$pictures = explode('|', $data['picture']);
        
        			$adInfo = array();
        			        			
        			if($data['price_add'] == 'RESERVED') {
        				$currentPrice = "<b>Gereserveerd</b>";
        			} elseif($data['price_add'] == 'MIN_BID') {
        				$currentPrice = "<b>Bieden vanaf ". formatPrice($data['price']) ."</b>";
        			} elseif($data['price_add'] == 'SEE_DESCRIPTION') {
        				$currentPrice = "<b>Zie beschrijving</b>";
        			} elseif($data['price_add'] == 'FAST_BID') {
        				$currentPrice = "<b>Bieden</b>";
        			} else {
        				$currentPrice = "<b>". formatPrice($data['price']) ."</b>";
        			}
        			
        			$adInfo[] = $currentPrice.($changedPrijs ? ' <s>'. formatPrice($oldData['prijs']) .'</s>' : '');
        			$adInfo[] = "<i><a href='http://verkopers.marktplaats.nl/". $data['verkoper_id'] ."'>". $data['verkoper'] ."</a></i>";
        			$adInfo[] = "<a href='http://maps.google.nl/maps?q=". $data['plaats'] ."%2C+Nederland&z=9'>". $data['plaats'] ."</a>". ($data['afstand'] > 0 ? ' ('. $data['afstand'] ." km)": '');
        			$adInfo[] = strftime("%a %e %b %H:%M", $data['date']);        
        			if(isset($data['status']) AND $data['status'] != '')  			$adInfo[] = $data['status'].($changedStatus ? ' <s>'. $oldData['status'] .'</s>' : '');
        			if(isset($data['transport']) AND $data['transport'] != '')	$adInfo[] = $data['transport'].($changedTransport ? ' <s>'. $oldData['transport'] .'</s>' : '');
        			      
        			$PlainItem = strtoupper($data['title']). "\n";
        			$PlainItem .= makeTextBlock($data['descr_long'], 500). "\n";
        			$PlainItem .= $data['price']. "\n";
        			$PlainItem .= $data['plaats']. " (".  $data['afstand'] ." km)\n";
        			$PlainItem .= $data['URL_short'];                
        			
        			$Item = "\n";
        			$Item .= '<!-- '. $data['key'] ." -->\n";
        			$Item .= "<table width='100%'>\n";
        			$Item .= "<tr>\n";
        			$Item .= " <td align='left'><a href='". $data['URL_short'] ."'><b>". $data['title'] .'</b></a>'. ($changedTitle ? ' <s>'. urldecode($oldData['title']) .'</s>' : '') . ($changedData ? ' (gewijzigd)' : '') ."</td>\n";       
        			$Item .= "</tr>\n";
        			$Item .= "<tr>\n";
        			$Item .= " <td align='right'>". implode(' | ', $adInfo) ."</td>\n";
        			$Item .= "</tr>\n";        
        			$Item .= "<tr>\n";
        			$Item .= " <td>". makeTextBlock($data['descr_long'], 500) ."</td>\n";
        			$Item .= "</tr>\n";
        			$Item .= "<tr>\n";
        			$Item .= " <td>\n";
        			$Item .= " <table>\n";
        			$Item .= " <tr>\n";
        			
        			foreach($pictures as $key => $foto) {
        			 // 0 -> width | 1 -> height
        			 $size = getimagesize('http:'.$foto);
        			 
        			 if($size[0] > $size[1]) {
        			  $atr = 'width="100"';
        			 } else {
        			  $atr = 'height="100"';
        			 }
        			 
        			 $Item .= "  <td><a href='http:". str_replace('_82.', '_85.', $foto) ."'><img src='http:$foto' $atr></a></td>\n";
        			 
        			 if(fmod($key, 3) == 2) {
        			  $Item .= " </tr>\n";
        			  $Item .= " <tr>\n";
        			 }
        			}
        			
        			$Item .= " </tr>\n";
        			$Item .= " </table>\n";
        			$Item .= " </td>\n";
        			$Item .= "</tr>\n";
        			$Item .= "</table>\n";
        			            
        			$PlainMessage[] = $PlainItem;
        			$HTMLMessage[] = showBlock($Item);
        		}
        		
        		if($debug == 0) {
        			if($changedPrijs OR $changedTitle OR $changedStatus OR $changedTransport) {
        				$teller_c++;
        			} else {
        				$teller_n++;
        			}
        		}
        	} else {
        		$teller_b++;
        	}
        	
        	$teller_p++;
      
      		if($debug == 1) {
      			echo $marktplaatsID. ": '<a href='". $basicData['URL_short'] ."'>". $data['title'] ."</a>'";
      			if($newItem) {
      				echo " is nieuw : ". strftime("%a %e %b %H:%M", $data['date']);
      			} elseif($changedTitle) {
      				echo " heeft gewijzigde titel";
      			} elseif($changedPrijs) {
      				echo " heeft gewijzigde prijs";
      			} elseif($changedStatus) {
      				echo " heeft gewijzigde status";
      			} elseif($changedTransport) {
      				echo " heeft gewijzigd transport";
      			} else {
      				echo " bestaat al";
      			}
      			
      			if($opnemenInMail) {
      				echo ", gaat mee in de mail<br>\n";
      			} else {
      				echo ", valt buiten de criteria<br>\n";
      			}      				
      		}
      		
      		$status = array(
      			'new' => $newItem,
       			'title' => $changedTitle,
     			  'prijs' => $changedPrijs,
     			  'status' => $changedStatus,
     			  'transport' => $changedTransport
     			 );
     			 
     			 if($debug == 0) {
     			 	AddUpdateData($data, $term, $status);
     			}
     		} elseif(!isset($advertentie['location']['cityName']) AND $debug != 0) {
     			echo $marktplaatsID. ": geen plaatsnaam bekend<br>";
     		} elseif(in_array($marktplaatsID, $foundIDs) AND $debug != 0) {
     			echo $marktplaatsID. ": al eerder gevonden<br>";
     		}
   		}
   		     
   		# Zolang er een link is naar een volgende pagina doorgaan
   		# Om te voorkomen dat hij mogelijk eindeloos doorgaat een maximum ingebouwd van 10 pagina   		   		
   		if($newFound AND $p < 10) {
   			writeToLog($term, 'Einde pagina '. $p .' ('. $teller_p .' resultaten)');
   			
   			$nextPage  = true;
   			$p++;
   		} else {
   			$nextPage  = false;
   			if($debug != 0)	echo 'Laatste pagina, niks nieuws gevonden';
   		}
   	}
   	
   	writeToLog($term, 'Totaal aantal gevonden resulaten : '. ($teller_c+$teller_n+$teller_b));
   	
   	if($teller_n > 0 OR $teller_c > 0 OR $debug == 1) {
   		if($rss == 1 OR $rss == 2) {
   			makeRSSFeed($term, '');
   			writeToLog($term, 'RSS-feed geupdate');
   		}
   		
   		if($rss == 0 OR $rss == 2) {
   			$PlainFooter = "\n";
    		$PlainFooter .= "$strCheckCommand   : ". $ScriptRoot. "admin/edit.php?id=$term\n";
    		$PlainFooter .= "$strCheckResults : ". $URL;
    		$PlainFooter .= "\n\n";
    		$PlainFooter .= $ScriptTitle.' '.$Version ."\n";
    		$PlainFooter .= "© ". (date("Y") != 2006 ? '2006-' : ''). date("Y") ." Matthijs Draijer";
    		
    		$FooterText = " <table width=100%>\n";
    		$FooterText .= " <tr>\n";
    		$FooterText .= "  <td align='left'><a href='". $ScriptRoot ."admin/edit.php?id=$term'>$strCheckCommand</a> | <a href='$URL'>$strCheckResults</a> | <a href='". $ScriptRoot ."admin/GoogleMaps.php?term=$term'>Google Maps</a> | <a href='". $ScriptRoot ."RSS/". $ZoekData['key'] .".xml'>RSS-feed</a></td>\n";
    		$FooterText .= "  <td align='right'>© ". (date("Y") != 2006 ? '2006-' : ''). date("Y") ." <a href='mailto:Matthijs Draijer <hotscripts@draijer.org>?Subject=Opmerking over $ScriptTitle $Version'>Matthijs Draijer</a></td>\n";
    		$FooterText .= " </tr>\n";
    		$FooterText .= " </table>\n";
    		
    		$HTMLFooter = "<tr>\n";
				$HTMLFooter .= " <td>&nbsp;</td>\n";
    		$HTMLFooter .= "</tr>\n";    
    		$HTMLFooter .= "<tr>\n";
    		$HTMLFooter .= "	<td align='center'>". showBlock($FooterText) ."</td>\n";
    		$HTMLFooter .= "</tr>\n";
    		$HTMLFooter .= "</table>\n";   
    		$HTMLFooter .= "</body>\n";
    		$HTMLFooter .= "</html>\n";
    		$HTMLFooter .= "\n\n<!--     Deze pagina is onderdeel van $ScriptTitle $Version gemaakt door Matthijs Draijer     -->";
    		   
      	$PlainMail  = $PlainHeader . implode("\n\n--- --- --- --- ---\n\n", $PlainMessage) . $PlainFooter;
		    
		    $HTMLMail = $HTMLHeader;
		    $HTMLMail .= "<tr>\n";		    
		    $HTMLMail .= "	<td width='480px' valign='top' align='center'>". implode("\n<p>\n", $HTMLMessage) ."</td>\n";
		    $HTMLMail .= "</tr>\n";
		    $HTMLMail .= $HTMLFooter;		    		    
		    
		    if($debug == 0) {
		    	if($teller_n != 0) {
		    		$Subjects[] = $teller_n . " ". ($teller_n == 1 ? $strCheckItemNew : $strCheckItemsNew);
		    	}
		    	
		    	if($teller_c != 0) {
		    		$Subjects[] = $teller_c . " ". ($teller_c == 1 ? $strCheckItemChanged : $strCheckItemsChanged);      
		    	}
     	
     			$mail = new PHPMailer;
     			$mail->From     = $ScriptMailAdress;
     			$mail->FromName = $ScriptTitle;
     			$mail->WordWrap = 90;
     			$mail->AddAddress($UserData['mailadres'], $UserData['naam']);
     			$mail->Subject = $SubjectPrefix . implode(' en ', $Subjects) ." $strCheckSubject '". getZoekString($term) ."'";
     			
     			if($ZoekData['CC'] != '') {
     				$mail->AddCC($ZoekData['CC']);
     			}     
     			
     			if($UserData['HTML'] == 1) {
     				$mail->IsHTML(true);
     				$mail->Body   = $HTMLMail;
     				$mail->AltBody = $PlainMail;
     			} else {
     				$mail->Body = $PlainMail;
     			}
     			
     			if(!$mail->Send()) {
     			 	echo date("H:i") . " : $strMailError '". getZoekString($term) ."' ($term).<br>";
     			 	writeToLog($term, $strLogMailError . ' ('. $UserData['naam'] .')');
     			} else {
     			 	echo date("H:i") . " : $strMailOkay '". getZoekString($term) ."' ($term).<br>";
     			 	writeToLog($term, $strLogMailOkay . ' ('. $UserData['naam'] .')');
     			}
    		} else {    			
    			echo $HTMLMail;
    			echo $teller_p;
    		}
    	}
		} else {
			if($debug == 0) {
    		echo date("H:i") . " : $strCheckOkay '". getZoekString($term) ."' ($term).<br>";
    		writeToLog($term, $strLogChecked);
   		}
  	}
	}
} else {
	echo $strCheckNoCheck;
}

include ('include/inc_footer.php');

?>
