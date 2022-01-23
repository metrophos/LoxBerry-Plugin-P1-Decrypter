#!/usr/bin/perl

use strict;
use warnings;
use CGI;
use LoxBerry::System;
use LoxBerry::Web;
use MIME::Base64;
use Config::Simple;

## on/off switch values
my @switch = ('0', '1');
my %switchLabels = (
    '0' => 'No',
    '1' => 'Yes'
);

# get configs
my $p1decrypterCfg = new Config::Simple("$lbpconfigdir/p1decrypter.cfg");
my $p1decrypterDefaultCfg = new Config::Simple("$lbpconfigdir/p1decrypter-default.cfg");
my $generalCfg = new Config::Simple("$lbsconfigdir/general.cfg");
my $plugindata = LoxBerry::System::plugindata();

# get request values
my $cgi = CGI->new;
$cgi->import_names('R');

# save settings to p1decrypter.cfg
if ($R::action eq "Save & Restart") {
    $p1decrypterCfg->param('P1DECRYPTER.ENABLED', $R::enabled);
    $p1decrypterCfg->param('P1DECRYPTER.KEY', $R::key);
    $p1decrypterCfg->param('P1DECRYPTER.MAPPING', encode_base64($R::mapping));
    $p1decrypterCfg->param('P1DECRYPTER.MINISERVER_ID', $R::miniserver_id);
    $p1decrypterCfg->param('P1DECRYPTER.UDP_PORT', $R::upd_port);

    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_PORT', $R::serial_input_port);
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_BAUDRATE', $R::serial_input_baudrate);
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_PARITY', $R::serial_input_parity);
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_STOPBITS', $R::serial_input_stopbits);
    $p1decrypterCfg->param('P1DECRYPTER.AAD', $R::aad);
    $p1decrypterCfg->param('P1DECRYPTER.SEND_TO_UDP', $R::send_to_udp);
    $p1decrypterCfg->param('P1DECRYPTER.UDP_HOST', $R::udp_host);
    $p1decrypterCfg->param('P1DECRYPTER.SEND_TO_SERIAL_PORT', $R::send_to_serial_port);
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_PORT', $R::serial_output_port);
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_BAUDRATE', $R::serial_output_baudrate);
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_PARITY', $R::serial_output_parity);
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_STOPBITS', $R::serial_output_stopbits);
    $p1decrypterCfg->param('P1DECRYPTER.RAW', $R::raw);
    $p1decrypterCfg->param('P1DECRYPTER.VERBOSE', $R::verbose);

    $p1decrypterCfg->save();
}

# reset values to p1decrypter-default.cfg
if ($R::action eq "Reset default configruation") {
    $p1decrypterCfg->param('P1DECRYPTER.ENABLED', $p1decrypterDefaultCfg->param('P1DECRYPTER.ENABLED'));
    $p1decrypterCfg->param('P1DECRYPTER.KEY', $p1decrypterDefaultCfg->param('P1DECRYPTER.KEY'));
    $p1decrypterCfg->param('P1DECRYPTER.MAPPING', $p1decrypterDefaultCfg->param('P1DECRYPTER.MAPPING'));
    $p1decrypterCfg->param('P1DECRYPTER.MINISERVER_ID', $p1decrypterDefaultCfg->param('P1DECRYPTER.MINISERVER_ID'));
    $p1decrypterCfg->param('P1DECRYPTER.UDP_PORT', $p1decrypterDefaultCfg->param('P1DECRYPTER.UDP_PORT'));

    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_PORT', $p1decrypterDefaultCfg->param('P1DECRYPTER.SERIAL_INPUT_PORT'));
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_BAUDRATE', $p1decrypterDefaultCfg->param('P1DECRYPTER.SERIAL_INPUT_BAUDRATE'));
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_PARITY', $p1decrypterDefaultCfg->param('P1DECRYPTER.SERIAL_INPUT_PARITY'));
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_STOPBITS', $p1decrypterDefaultCfg->param('P1DECRYPTER.SERIAL_INPUT_STOPBITS'));
    $p1decrypterCfg->param('P1DECRYPTER.AAD', $p1decrypterDefaultCfg->param('P1DECRYPTER.AAD'));
    $p1decrypterCfg->param('P1DECRYPTER.SEND_TO_UDP', $p1decrypterDefaultCfg->param('P1DECRYPTER.SEND_TO_UDP'));
    $p1decrypterCfg->param('P1DECRYPTER.UDP_HOST', $p1decrypterDefaultCfg->param('P1DECRYPTER.UDP_HOST'));
    $p1decrypterCfg->param('P1DECRYPTER.SEND_TO_SERIAL_PORT', $p1decrypterDefaultCfg->param('P1DECRYPTER.SEND_TO_SERIAL_PORT'));
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_PORT', $p1decrypterDefaultCfg->param('P1DECRYPTER.SERIAL_OUTPUT_PORT'));
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_BAUDRATE', $p1decrypterDefaultCfg->param('P1DECRYPTER.SERIAL_OUTPUT_BAUDRATE'));
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_PARITY', $p1decrypterDefaultCfg->param('P1DECRYPTER.SERIAL_OUTPUT_PARITY'));
    $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_STOPBITS', $p1decrypterDefaultCfg->param('P1DECRYPTER.SERIAL_OUTPUT_STOPBITS'));
    $p1decrypterCfg->param('P1DECRYPTER.RAW', $p1decrypterDefaultCfg->param('P1DECRYPTER.RAW'));
    $p1decrypterCfg->param('P1DECRYPTER.VERBOSE', $p1decrypterDefaultCfg->param('P1DECRYPTER.VERBOSE'));

    $p1decrypterCfg->save();
}

# read settings from p1decrypter.cfg
$cgi->delete_all();
$R::enabled = $p1decrypterCfg->param('P1DECRYPTER.ENABLED');
$R::key = $p1decrypterCfg->param('P1DECRYPTER.KEY');
$R::mapping = decode_base64($p1decrypterCfg->param('P1DECRYPTER.MAPPING'));
$R::miniserver_id = $p1decrypterCfg->param('P1DECRYPTER.MINISERVER_ID');
$R::upd_port = $p1decrypterCfg->param('P1DECRYPTER.UDP_PORT');

$R::serial_input_port = $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_PORT');
$R::serial_input_baudrate = $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_BAUDRATE');
$R::serial_input_parity = $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_PARITY');
$R::serial_input_stopbits = $p1decrypterCfg->param('P1DECRYPTER.SERIAL_INPUT_STOPBITS');
$R::aad = $p1decrypterCfg->param('P1DECRYPTER.AAD');
$R::send_to_udp = $p1decrypterCfg->param('P1DECRYPTER.SEND_TO_UDP');
$R::udp_host = $p1decrypterCfg->param('P1DECRYPTER.UDP_HOST');
$R::send_to_serial_port = $p1decrypterCfg->param('P1DECRYPTER.SEND_TO_SERIAL_PORT');
$R::serial_output_port = $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_PORT');
$R::serial_output_baudrate = $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_BAUDRATE');
$R::serial_output_parity = $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_PARITY');
$R::serial_output_stopbits = $p1decrypterCfg->param('P1DECRYPTER.SERIAL_OUTPUT_STOPBITS');
$R::raw = $p1decrypterCfg->param('P1DECRYPTER.RAW');
$R::verbose = $p1decrypterCfg->param('P1DECRYPTER.VERBOSE');

# restart p1decrypter
if ($R::action eq "Save & Restart" || $R::action eq "Reset default configruation") {
    if ($R::enabled eq "1") {
        qx(pkill -9 -f p1decrypter.py);
        qx(/bin/bash $lbhomedir/system/cron/cron.05min/$plugindata->{PLUGINDB_NAME} $R::enabled > /dev/null 2>&1 &);
        sleep(2);
    }
    else {
        qx(pkill -9 -f p1decrypter.py);
    }
}

#--------------------------------------------------
#--------------------------------------------------

# create html elements
my $template = HTML::Template->new(
    filename          => "$lbptemplatedir/content.html",
    associate         => $cgi,
);

## ENABLED switch
$template->param(ENABLED => $cgi->popup_menu(
    -name    => 'enabled',
    -values  => \@switch,
    -labels  => \%switchLabels,
    -default => $R::enabled
));

## KEY textfield
$template->param(KEY => $cgi->textfield(-name => 'key', -default => $R::key));

## MAPPING textarea
$template->param(MAPPING => $cgi->textarea(-name => 'mapping', -default => $R::mapping));

## MINISERVER_ID selection
my @miniserverIds = ();
my %miniserverLabels = ();
for (my $i = 1; $i <= $generalCfg->param('BASE.MINISERVERS'); $i++) {
    push @miniserverIds, $i;
    $miniserverLabels{ $i } = $generalCfg->param("MINISERVER$i.NAME") . " (" . ($generalCfg->param("MINISERVER$i.IPADDRESS")) . ")";
};
$template->param(MINISERVER_ID => $cgi->popup_menu(
    -name    => 'miniserver_id',
    -values  => \@miniserverIds,
    -labels  => \%miniserverLabels,
    -default => $R::miniserver_id
));

## UDP_PORT textfield
$template->param(UDP_PORT => $cgi->textfield(-name => 'upd_port', -default => $R::upd_port));

## SERIAL_INPUT_PORT textfield
$template->param(SERIAL_INPUT_PORT => $cgi->textfield(-name => 'serial_input_port', -default => $R::serial_input_port));

## SERIAL_INPUT_BAUDRATE textfield
$template->param(SERIAL_INPUT_BAUDRATE => $cgi->textfield(-name => 'serial_input_baudrate', -default => $R::serial_input_baudrate));

## SERIAL_INPUT_PARITY textfield
$template->param(SERIAL_INPUT_PARITY => $cgi->textfield(-name => 'serial_input_parity', -default => $R::serial_input_parity));

## SERIAL_INPUT_STOPBITS textfield
$template->param(SERIAL_INPUT_STOPBITS => $cgi->textfield(-name => 'serial_input_stopbits', -default => $R::serial_input_stopbits));

## AAD textfield
$template->param(AAD => $cgi->textfield(-name => 'aad', -default => $R::aad));

## SEND_TO_UDP switch
$template->param(SEND_TO_UDP => $cgi->popup_menu(
    -name    => 'send_to_udp',
    -values  => \@switch,
    -labels  => \%switchLabels,
    -default => $R::send_to_udp
));

## UDP_HOST textfield
$template->param(UDP_HOST => $cgi->textfield(-name => 'udp_host', -default => $R::udp_host));

## SEND_TO_SERIAL_PORT switch
$template->param(SEND_TO_SERIAL_PORT => $cgi->popup_menu(
    -name    => 'send_to_serial_port',
    -values  => \@switch,
    -labels  => \%switchLabels,
    -default => $R::send_to_serial_port
));

## SERIAL_OUTPUT_PORT textfield
$template->param(SERIAL_OUTPUT_PORT => $cgi->textfield(-name => 'serial_output_port', -default => $R::serial_output_port));

## SERIAL_OUTPUT_BAUDRATE textfield
$template->param(SERIAL_OUTPUT_BAUDRATE => $cgi->textfield(-name => 'serial_output_baudrate', -default => $R::serial_output_baudrate));

## SERIAL_OUTPUT_PARITY textfield
$template->param(SERIAL_OUTPUT_PARITY => $cgi->textfield(-name => 'serial_output_parity', -default => $R::serial_output_parity));

## SERIAL_OUTPUT_STOPBITS textfield
$template->param(SERIAL_OUTPUT_STOPBITS => $cgi->textfield(-name => 'serial_output_stopbits', -default => $R::serial_output_stopbits));

## RAW switch
$template->param(RAW => $cgi->popup_menu(
    -name    => 'raw',
    -values  => \@switch,
    -labels  => \%switchLabels,
    -default => $R::raw
));

## VERBOSE switch
$template->param(VERBOSE => $cgi->popup_menu(
    -name    => 'verbose',
    -values  => \@switch,
    -labels  => \%switchLabels,
    -default => $R::verbose
));

## pid
my $pid = trim(qx(pgrep -f p1decrypter.py));
$pid = $pid eq "" ? "<span style=\"color:red\">$plugindata->{PLUGINDB_TITLE} down</span>" : "<span style=\"color:green\">$plugindata->{PLUGINDB_TITLE} up (PID: $pid)</span>";
$template->param(PID => $pid);


# write template
LoxBerry::Web::lbheader("$plugindata->{PLUGINDB_TITLE} $plugindata->{PLUGINDB_VERSION}", "https://github.com/metrophos/LoxBerry-Plugin-P1-Decrypter");
print $template->output();
LoxBerry::Web::lbfooter();

exit;
