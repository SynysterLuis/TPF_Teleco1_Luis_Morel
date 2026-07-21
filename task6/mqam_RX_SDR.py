#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: Luis
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import blocks
from gnuradio import channels
from gnuradio.filter import firdes
from gnuradio import digital
from gnuradio import filter
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network
from gnuradio import soapy
import math
import sip
import threading



class mqam_RX_SDR(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "mqam_RX_SDR")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.symbol_rate = symbol_rate = 2e5
        self.samp_rate = samp_rate = 2e6
        self.sps = sps = int(samp_rate / symbol_rate)
        self.snr_db = snr_db = 40
        self.rolloff = rolloff = 0.35
        self.M = M = 16
        self.tx_delay = tx_delay = 5
        self.ted_gain = ted_gain = 1
        self.sample_phase_sdr = sample_phase_sdr = 0
        self.sample_phase = sample_phase = 2
        self.rx_tune = rx_tune = -36000
        self.rx_scale = rx_scale = 0.2
        self.rx_gain = rx_gain = 40
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(
            sps,
            samp_rate,
            symbol_rate,
            rolloff,
            11*sps
        )
        self.qam_const = qam_const = digital.constellation_16qam().base()
        self.qam_const.set_npwr(1.0)
        self.noise_voltage = noise_voltage = 10**(-snr_db/20.0)
        self.freq = freq = 433e6
        self.fine_freq = fine_freq = 0
        self.costas = costas = 0.001
        self.bits_per_symbol = bits_per_symbol = int(math.log2(M))
        self.ber_window = ber_window = 10000

        ##################################################
        # Blocks
        ##################################################

        self._rx_tune_range = qtgui.Range(-100000, 100000, 1000, -36000, 200)
        self._rx_tune_win = qtgui.RangeWidget(self._rx_tune_range, self.set_rx_tune, "Corrección RX [Hz]", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rx_tune_win)
        self._rx_scale_range = qtgui.Range(0.1, 20, 0.1, 0.2, 200)
        self._rx_scale_win = qtgui.RangeWidget(self._rx_scale_range, self.set_rx_scale, "Corrección RX  en escala", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rx_scale_win)
        self._rx_gain_range = qtgui.Range(0, 50, 1, 40, 200)
        self._rx_gain_win = qtgui.RangeWidget(self._rx_gain_range, self.set_rx_gain, "Ganancia RTL-SDR [dB]", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rx_gain_win)
        self._tx_delay_range = qtgui.Range(0, 200, 1, 5, 200)
        self._tx_delay_win = qtgui.RangeWidget(self._tx_delay_range, self.set_tx_delay, "Alineación TX-RX", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tx_delay_win)
        self._ted_gain_range = qtgui.Range(0.01, 3, 0.01, 1, 200)
        self._ted_gain_win = qtgui.RangeWidget(self._ted_gain_range, self.set_ted_gain, "Ganancia esperada TED", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._ted_gain_win)
        self.soapy_rtlsdr_source_0 = None
        dev = 'driver=rtlsdr'
        stream_args = 'bufflen=16384'
        tune_args = ['']
        settings = ['']

        def _set_soapy_rtlsdr_source_0_gain_mode(channel, agc):
            self.soapy_rtlsdr_source_0.set_gain_mode(channel, agc)
            if not agc:
                  self.soapy_rtlsdr_source_0.set_gain(channel, self._soapy_rtlsdr_source_0_gain_value)
        self.set_soapy_rtlsdr_source_0_gain_mode = _set_soapy_rtlsdr_source_0_gain_mode

        def _set_soapy_rtlsdr_source_0_gain(channel, name, gain):
            self._soapy_rtlsdr_source_0_gain_value = gain
            if not self.soapy_rtlsdr_source_0.get_gain_mode(channel):
                self.soapy_rtlsdr_source_0.set_gain(channel, gain)
        self.set_soapy_rtlsdr_source_0_gain = _set_soapy_rtlsdr_source_0_gain

        def _set_soapy_rtlsdr_source_0_bias(bias):
            if 'biastee' in self._soapy_rtlsdr_source_0_setting_keys:
                self.soapy_rtlsdr_source_0.write_setting('biastee', bias)
        self.set_soapy_rtlsdr_source_0_bias = _set_soapy_rtlsdr_source_0_bias

        self.soapy_rtlsdr_source_0 = soapy.source(dev, "fc32", 1, 'driver=rtlsdr',
                                  stream_args, tune_args, settings)

        self._soapy_rtlsdr_source_0_setting_keys = [a.key for a in self.soapy_rtlsdr_source_0.get_setting_info()]

        self.soapy_rtlsdr_source_0.set_sample_rate(0, samp_rate)
        self.soapy_rtlsdr_source_0.set_frequency(0, (freq + rx_tune))
        self.soapy_rtlsdr_source_0.set_frequency_correction(0, 0)
        self.set_soapy_rtlsdr_source_0_bias(bool(False))
        self._soapy_rtlsdr_source_0_gain_value = rx_gain
        self.set_soapy_rtlsdr_source_0_gain_mode(0, bool(False))
        self.set_soapy_rtlsdr_source_0_gain(0, 'TUNER', rx_gain)
        self._snr_db_range = qtgui.Range(0, 40, 1, 40, 200)
        self._snr_db_win = qtgui.RangeWidget(self._snr_db_range, self.set_snr_db, "SNR aproximada [dB]", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._snr_db_win)
        self._sample_phase_sdr_range = qtgui.Range(0, 9, 1, 0, 200)
        self._sample_phase_sdr_win = qtgui.RangeWidget(self._sample_phase_sdr_range, self.set_sample_phase_sdr, "Fase de SDR", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sample_phase_sdr_win)
        self._sample_phase_range = qtgui.Range(0, 9, 1, 2, 200)
        self._sample_phase_win = qtgui.RangeWidget(self._sample_phase_range, self.set_sample_phase, "Fase de muestreo", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sample_phase_win)
        self.qtgui_time_sink_x_4 = qtgui.time_sink_c(
            1024, #size
            samp_rate, #samp_rate
            "Señal recibida Tiempo", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_4.set_update_time(0.10)
        self.qtgui_time_sink_x_4.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_4.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_4.enable_tags(True)
        self.qtgui_time_sink_x_4.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_4.enable_autoscale(False)
        self.qtgui_time_sink_x_4.enable_grid(True)
        self.qtgui_time_sink_x_4.enable_axis_labels(True)
        self.qtgui_time_sink_x_4.enable_control_panel(False)
        self.qtgui_time_sink_x_4.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_time_sink_x_4.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_x_4.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_x_4.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_4.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_4.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_4.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_4.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_4.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_4_win = sip.wrapinstance(self.qtgui_time_sink_x_4.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_4_win)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
            1024, #size
            samp_rate, #samp_rate
            "Numeros recibidos", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(True)
        self.qtgui_time_sink_x_0.enable_grid(True)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_0_win)
        self.qtgui_number_sink_1 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_1.set_update_time(0.10)
        self.qtgui_number_sink_1.set_title("Potencia media RX")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_1.set_min(i, -1)
            self.qtgui_number_sink_1.set_max(i, 1)
            self.qtgui_number_sink_1.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_1.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_1.set_label(i, labels[i])
            self.qtgui_number_sink_1.set_unit(i, units[i])
            self.qtgui_number_sink_1.set_factor(i, factor[i])

        self.qtgui_number_sink_1.enable_autoscale(False)
        self._qtgui_number_sink_1_win = sip.wrapinstance(self.qtgui_number_sink_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_1_win)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Frequency Sink RF", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(True)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.qtgui_const_sink_x_2_0_0 = qtgui.const_sink_c(
            1024, #size
            "RX con PRE - Symbol Sync", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_2_0_0.set_update_time(0.10)
        self.qtgui_const_sink_x_2_0_0.set_y_axis((-1.5), 1.5)
        self.qtgui_const_sink_x_2_0_0.set_x_axis((-1.5), 1.5)
        self.qtgui_const_sink_x_2_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_2_0_0.enable_autoscale(False)
        self.qtgui_const_sink_x_2_0_0.enable_grid(True)
        self.qtgui_const_sink_x_2_0_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_2_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_2_0_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_2_0_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_2_0_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_2_0_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_2_0_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_2_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_2_0_0_win = sip.wrapinstance(self.qtgui_const_sink_x_2_0_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_2_0_0_win)
        self.qtgui_const_sink_x_2_0 = qtgui.const_sink_c(
            1024, #size
            "RX con Symbol Sync", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_2_0.set_update_time(0.10)
        self.qtgui_const_sink_x_2_0.set_y_axis((-1.5), 1.5)
        self.qtgui_const_sink_x_2_0.set_x_axis((-1.5), 1.5)
        self.qtgui_const_sink_x_2_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_2_0.enable_autoscale(False)
        self.qtgui_const_sink_x_2_0.enable_grid(True)
        self.qtgui_const_sink_x_2_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_2_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_2_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_2_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_2_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_2_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_2_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_2_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_2_0_win = sip.wrapinstance(self.qtgui_const_sink_x_2_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_2_0_win)
        self.network_udp_sink_0 = network.udp_sink(gr.sizeof_char, 1, '127.0.0.1', 6001, 0, 1316, False)
        self.interp_fir_filter_xxx_1 = filter.interp_fir_filter_ccc(1, rrc_taps)
        self.interp_fir_filter_xxx_1.declare_sample_delay(0)
        self._fine_freq_range = qtgui.Range(-3000, 3000, 10, 0, 200)
        self._fine_freq_win = qtgui.RangeWidget(self._fine_freq_range, self.set_fine_freq, "Corrección fina [Hz]", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._fine_freq_win)
        self.filter_fft_low_pass_filter_0 = filter.fft_filter_ccc(1, firdes.low_pass(1, samp_rate, 300000, 50000, window.WIN_HAMMING, 6.76), 1)
        self.digital_symbol_sync_xx_0 = digital.symbol_sync_cc(
            digital.TED_GARDNER,
            sps,
            0.02,
            1.0,
            0.3,
            2.5,
            1,
            digital.constellation_bpsk().base(),
            digital.IR_MMSE_8TAP,
            128,
            [])
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(0.01, 4, False)
        self.digital_constellation_decoder_cb_0 = digital.constellation_decoder_cb(qam_const)
        self._costas_range = qtgui.Range(0.001, 0.02, 0.001, 0.001, 200)
        self._costas_win = qtgui.RangeWidget(self._costas_range, self.set_costas, "Ancho costas", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._costas_win)
        self.channels_channel_model_0 = channels.channel_model(
            noise_voltage=noise_voltage,
            frequency_offset=0.0,
            epsilon=1.0,
            taps=[1.0 + 0.0j],
            noise_seed=0,
            block_tags=True)
        self.blocks_uchar_to_float_0 = blocks.uchar_to_float()
        self.blocks_repack_bits_bb_1 = blocks.repack_bits_bb(bits_per_symbol, 8, "", False, gr.GR_MSB_FIRST)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_cc(rx_scale)
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(10000, (1.0/10000), 4000, 1)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.qtgui_number_sink_1, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.digital_symbol_sync_xx_0, 0))
        self.connect((self.blocks_repack_bits_bb_1, 0), (self.blocks_uchar_to_float_0, 0))
        self.connect((self.blocks_repack_bits_bb_1, 0), (self.network_udp_sink_0, 0))
        self.connect((self.blocks_uchar_to_float_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.channels_channel_model_0, 0), (self.interp_fir_filter_xxx_1, 0))
        self.connect((self.digital_constellation_decoder_cb_0, 0), (self.blocks_repack_bits_bb_1, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_constellation_decoder_cb_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.qtgui_const_sink_x_2_0, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.filter_fft_low_pass_filter_0, 0), (self.channels_channel_model_0, 0))
        self.connect((self.interp_fir_filter_xxx_1, 0), (self.blocks_multiply_const_vxx_0_0, 0))
        self.connect((self.interp_fir_filter_xxx_1, 0), (self.qtgui_const_sink_x_2_0_0, 0))
        self.connect((self.soapy_rtlsdr_source_0, 0), (self.filter_fft_low_pass_filter_0, 0))
        self.connect((self.soapy_rtlsdr_source_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.soapy_rtlsdr_source_0, 0), (self.qtgui_time_sink_x_4, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "mqam_RX_SDR")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_symbol_rate(self):
        return self.symbol_rate

    def set_symbol_rate(self, symbol_rate):
        self.symbol_rate = symbol_rate
        self.set_rrc_taps(firdes.root_raised_cosine(
            self.sps,
            self.samp_rate,
            self.symbol_rate,
            self.rolloff,
            11*self.sps
        ))
        self.set_sps(int(self.samp_rate / self.symbol_rate))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_rrc_taps(firdes.root_raised_cosine(
            self.sps,
            self.samp_rate,
            self.symbol_rate,
            self.rolloff,
            11*self.sps
        ))
        self.set_sps(int(self.samp_rate / self.symbol_rate))
        self.filter_fft_low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 300000, 50000, window.WIN_HAMMING, 6.76))
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)
        self.qtgui_time_sink_x_4.set_samp_rate(self.samp_rate)
        self.soapy_rtlsdr_source_0.set_sample_rate(0, self.samp_rate)

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_rrc_taps(firdes.root_raised_cosine(
            self.sps,
            self.samp_rate,
            self.symbol_rate,
            self.rolloff,
            11*self.sps
        ))
        self.digital_symbol_sync_xx_0.set_sps(self.sps)

    def get_snr_db(self):
        return self.snr_db

    def set_snr_db(self, snr_db):
        self.snr_db = snr_db
        self.set_noise_voltage(10**(-self.snr_db/20.0))

    def get_rolloff(self):
        return self.rolloff

    def set_rolloff(self, rolloff):
        self.rolloff = rolloff
        self.set_rrc_taps(firdes.root_raised_cosine(
            self.sps,
            self.samp_rate,
            self.symbol_rate,
            self.rolloff,
            11*self.sps
        ))

    def get_M(self):
        return self.M

    def set_M(self, M):
        self.M = M
        self.set_bits_per_symbol(int(math.log2(self.M)))

    def get_tx_delay(self):
        return self.tx_delay

    def set_tx_delay(self, tx_delay):
        self.tx_delay = tx_delay

    def get_ted_gain(self):
        return self.ted_gain

    def set_ted_gain(self, ted_gain):
        self.ted_gain = ted_gain

    def get_sample_phase_sdr(self):
        return self.sample_phase_sdr

    def set_sample_phase_sdr(self, sample_phase_sdr):
        self.sample_phase_sdr = sample_phase_sdr

    def get_sample_phase(self):
        return self.sample_phase

    def set_sample_phase(self, sample_phase):
        self.sample_phase = sample_phase

    def get_rx_tune(self):
        return self.rx_tune

    def set_rx_tune(self, rx_tune):
        self.rx_tune = rx_tune
        self.soapy_rtlsdr_source_0.set_frequency(0, (self.freq + self.rx_tune))

    def get_rx_scale(self):
        return self.rx_scale

    def set_rx_scale(self, rx_scale):
        self.rx_scale = rx_scale
        self.blocks_multiply_const_vxx_0_0.set_k(self.rx_scale)

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain
        self.set_soapy_rtlsdr_source_0_gain(0, 'TUNER', self.rx_gain)

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps
        self.interp_fir_filter_xxx_1.set_taps(self.rrc_taps)

    def get_qam_const(self):
        return self.qam_const

    def set_qam_const(self, qam_const):
        self.qam_const = qam_const
        self.digital_constellation_decoder_cb_0.set_constellation(self.qam_const)

    def get_noise_voltage(self):
        return self.noise_voltage

    def set_noise_voltage(self, noise_voltage):
        self.noise_voltage = noise_voltage
        self.channels_channel_model_0.set_noise_voltage(self.noise_voltage)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.soapy_rtlsdr_source_0.set_frequency(0, (self.freq + self.rx_tune))

    def get_fine_freq(self):
        return self.fine_freq

    def set_fine_freq(self, fine_freq):
        self.fine_freq = fine_freq

    def get_costas(self):
        return self.costas

    def set_costas(self, costas):
        self.costas = costas

    def get_bits_per_symbol(self):
        return self.bits_per_symbol

    def set_bits_per_symbol(self, bits_per_symbol):
        self.bits_per_symbol = bits_per_symbol
        self.blocks_repack_bits_bb_1.set_k_and_l(self.bits_per_symbol,8)

    def get_ber_window(self):
        return self.ber_window

    def set_ber_window(self, ber_window):
        self.ber_window = ber_window




def main(top_block_cls=mqam_RX_SDR, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
