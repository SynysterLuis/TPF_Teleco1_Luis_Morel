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
def rectangular_qam_points(m):
    k = int(math.log2(m))
    bits_i = (k + 1) // 2
    bits_q = k // 2
    ni = 2**bits_i
    nq = 2**bits_q

    raw = [
        complex(2*i-(ni-1), 2*q-(nq-1))
        for q in range(nq)
        for i in range(ni)
    ]

    scale = math.sqrt(
        sum(abs(p)**2 for p in raw) / len(raw)
    )

    return [p/scale for p in raw]
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
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
from gnuradio import zeromq
import math
import sip
import threading



class mqam_RX_TCP(gr.top_block, Qt.QWidget):

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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "mqam_RX_TCP")

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
        self.symbol_rate = symbol_rate = 200000
        self.samp_rate = samp_rate = 2000000
        self.m_sel = m_sel = 0
        self.sps = sps = int(samp_rate / symbol_rate)
        self.snr_db = snr_db = 40
        self.rolloff = rolloff = 0.35
        self.qam8_points = qam8_points = rectangular_qam_points(8)
        self.qam64_points = qam64_points = rectangular_qam_points(64)
        self.qam32_points = qam32_points = rectangular_qam_points(32)
        self.qam256_points = qam256_points = rectangular_qam_points(256)
        self.qam128_points = qam128_points = rectangular_qam_points(128)
        self.M = M = [8, 16, 32, 64, 128, 256][m_sel]
        self.tx_delay = tx_delay = 5
        self.ted_gain = ted_gain = 1
        self.sample_phase = sample_phase = 2
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(
            sps,
            samp_rate,
            symbol_rate,
            rolloff,
            11*sps
        )
        self.qam_const = qam_const = digital.constellation_16qam().base()
        self.qam_const.set_npwr(1.0)
        self.qam8_const = qam8_const = digital.constellation_calcdist(
            qam8_points,
            list(range(len(qam8_points))),
            1,
            1
        ).base()
        self.qam64_const = qam64_const = digital.constellation_calcdist(
            qam64_points,
            list(range(len(qam64_points))),
            1,
            1
        ).base()
        self.qam32_const = qam32_const = digital.constellation_calcdist(
            qam32_points,
            list(range(len(qam32_points))),
            1,
            1
        ).base()
        self.qam256_const = qam256_const = digital.constellation_calcdist(
            qam256_points,
            list(range(len(qam256_points))),
            1,
            1
        ).base()
        self.qam128_const = qam128_const = digital.constellation_calcdist(
            qam128_points,
            list(range(len(qam128_points))),
            1,
            1
        ).base()
        self.noise_voltage = noise_voltage = 10**(-snr_db/20.0)
        self.medium = medium = 0
        self.freq = freq = 433e6
        self.bits_per_symbol = bits_per_symbol = int(math.log2(M))
        self.ber_window = ber_window = 10000

        ##################################################
        # Blocks
        ##################################################

        self._ted_gain_range = qtgui.Range(0.01, 1.0, 0.01, 1, 200)
        self._ted_gain_win = qtgui.RangeWidget(self._ted_gain_range, self.set_ted_gain, "Ganancia esperada TED", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._ted_gain_win)
        # Create the options list
        self._medium_options = [0, 1]
        # Create the labels list
        self._medium_labels = ['TCP / ZMQ', 'SDR']
        # Create the combo box
        self._medium_tool_bar = Qt.QToolBar(self)
        self._medium_tool_bar.addWidget(Qt.QLabel("Medio de transmisión" + ": "))
        self._medium_combo_box = Qt.QComboBox()
        self._medium_tool_bar.addWidget(self._medium_combo_box)
        for _label in self._medium_labels: self._medium_combo_box.addItem(_label)
        self._medium_callback = lambda i: Qt.QMetaObject.invokeMethod(self._medium_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._medium_options.index(i)))
        self._medium_callback(self.medium)
        self._medium_combo_box.currentIndexChanged.connect(
            lambda i: self.set_medium(self._medium_options[i]))
        # Create the radio buttons
        self.top_layout.addWidget(self._medium_tool_bar)
        # Create the options list
        self._m_sel_options = [0, 1, 2, 3, 4, 5]
        # Create the labels list
        self._m_sel_labels = ['8-QAM', '16-QAM', '32-QAM', '64-QAM', '128-QAM', '256-QAM']
        # Create the combo box
        self._m_sel_tool_bar = Qt.QToolBar(self)
        self._m_sel_tool_bar.addWidget(Qt.QLabel("Orden M-QAM" + ": "))
        self._m_sel_combo_box = Qt.QComboBox()
        self._m_sel_tool_bar.addWidget(self._m_sel_combo_box)
        for _label in self._m_sel_labels: self._m_sel_combo_box.addItem(_label)
        self._m_sel_callback = lambda i: Qt.QMetaObject.invokeMethod(self._m_sel_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._m_sel_options.index(i)))
        self._m_sel_callback(self.m_sel)
        self._m_sel_combo_box.currentIndexChanged.connect(
            lambda i: self.set_m_sel(self._m_sel_options[i]))
        # Create the radio buttons
        self.top_layout.addWidget(self._m_sel_tool_bar)
        self.zeromq_pull_source_0 = zeromq.pull_source(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:5555', 100, False, (-1), False)
        self._tx_delay_range = qtgui.Range(0, 200, 1, 5, 200)
        self._tx_delay_win = qtgui.RangeWidget(self._tx_delay_range, self.set_tx_delay, "Alineación TX-RX", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tx_delay_win)
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
        self.soapy_rtlsdr_source_0.set_frequency(0, freq)
        self.soapy_rtlsdr_source_0.set_frequency_correction(0, 0)
        self.set_soapy_rtlsdr_source_0_bias(bool(False))
        self._soapy_rtlsdr_source_0_gain_value = 20
        self.set_soapy_rtlsdr_source_0_gain_mode(0, bool(False))
        self.set_soapy_rtlsdr_source_0_gain(0, 'TUNER', 20)
        self._snr_db_range = qtgui.Range(0, 40, 1, 40, 200)
        self._snr_db_win = qtgui.RangeWidget(self._snr_db_range, self.set_snr_db, "SNR aproximada [dB]", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._snr_db_win)
        self._sample_phase_range = qtgui.Range(0, 9, 1, 2, 200)
        self._sample_phase_win = qtgui.RangeWidget(self._sample_phase_range, self.set_sample_phase, "Fase de muestreo", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sample_phase_win)
        self.qtgui_time_sink_x_1 = qtgui.time_sink_f(
            64, #size
            symbol_rate, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_1.set_update_time(0.10)
        self.qtgui_time_sink_x_1.set_y_axis(-1, 16)

        self.qtgui_time_sink_x_1.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1.enable_tags(True)
        self.qtgui_time_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_1.enable_autoscale(False)
        self.qtgui_time_sink_x_1.enable_grid(True)
        self.qtgui_time_sink_x_1.enable_axis_labels(True)
        self.qtgui_time_sink_x_1.enable_control_panel(False)
        self.qtgui_time_sink_x_1.enable_stem_plot(False)


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
                self.qtgui_time_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_win = sip.wrapinstance(self.qtgui_time_sink_x_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_1_win)
        self.qtgui_histogram_sink_x_0 = qtgui.histogram_sink_f(
            1024,
            16,
            (-0.5),
            15.5,
            "",
            1,
            None # parent
        )

        self.qtgui_histogram_sink_x_0.set_update_time(0.10)
        self.qtgui_histogram_sink_x_0.enable_autoscale(True)
        self.qtgui_histogram_sink_x_0.enable_accumulate(False)
        self.qtgui_histogram_sink_x_0.enable_grid(False)
        self.qtgui_histogram_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers= [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_histogram_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_histogram_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_histogram_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_histogram_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_histogram_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_histogram_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_histogram_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_histogram_sink_x_0_win = sip.wrapinstance(self.qtgui_histogram_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_histogram_sink_x_0_win)
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
        self.digital_symbol_sync_xx_0 = digital.symbol_sync_cc(
            digital.TED_GARDNER,
            sps,
            (2*math.pi/100),
            1.0,
            ted_gain,
            1.5,
            1,
            digital.constellation_bpsk().base(),
            digital.IR_MMSE_8TAP,
            128,
            [])
        self.digital_fll_band_edge_cc_0 = digital.fll_band_edge_cc(sps, rolloff, 32, 0.04)
        self.digital_constellation_decoder_cb_1_3 = digital.constellation_decoder_cb(qam64_const)
        self.digital_constellation_decoder_cb_1_2 = digital.constellation_decoder_cb(qam32_const)
        self.digital_constellation_decoder_cb_1_1 = digital.constellation_decoder_cb(qam128_const)
        self.digital_constellation_decoder_cb_1_0 = digital.constellation_decoder_cb(qam256_const)
        self.digital_constellation_decoder_cb_1 = digital.constellation_decoder_cb(qam8_const)
        self.digital_constellation_decoder_cb_0 = digital.constellation_decoder_cb(qam_const)
        self.channels_channel_model_0 = channels.channel_model(
            noise_voltage=noise_voltage,
            frequency_offset=0.0,
            epsilon=1.0,
            taps=[1.0 + 0.0j],
            noise_seed=0,
            block_tags=True)
        self.blocks_selector_1_0 = blocks.selector(gr.sizeof_char*1,m_sel,0)
        self.blocks_selector_1_0.set_enabled(True)
        self.blocks_selector_1 = blocks.selector(gr.sizeof_gr_complex*1,0,m_sel)
        self.blocks_selector_1.set_enabled(True)
        self.blocks_selector_0 = blocks.selector(gr.sizeof_gr_complex*1,medium,0)
        self.blocks_selector_0.set_enabled(True)
        self.blocks_repack_bits_bb_1 = blocks.repack_bits_bb(bits_per_symbol, 8, "", False, gr.GR_MSB_FIRST)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_cc(1.0 / sps)
        self.blocks_char_to_float_0 = blocks.char_to_float(1, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_char_to_float_0, 0), (self.qtgui_histogram_sink_x_0, 0))
        self.connect((self.blocks_char_to_float_0, 0), (self.qtgui_time_sink_x_1, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.digital_symbol_sync_xx_0, 0))
        self.connect((self.blocks_repack_bits_bb_1, 0), (self.network_udp_sink_0, 0))
        self.connect((self.blocks_selector_0, 0), (self.interp_fir_filter_xxx_1, 0))
        self.connect((self.blocks_selector_1, 1), (self.digital_constellation_decoder_cb_0, 0))
        self.connect((self.blocks_selector_1, 0), (self.digital_constellation_decoder_cb_1, 0))
        self.connect((self.blocks_selector_1, 5), (self.digital_constellation_decoder_cb_1_0, 0))
        self.connect((self.blocks_selector_1, 4), (self.digital_constellation_decoder_cb_1_1, 0))
        self.connect((self.blocks_selector_1, 2), (self.digital_constellation_decoder_cb_1_2, 0))
        self.connect((self.blocks_selector_1, 3), (self.digital_constellation_decoder_cb_1_3, 0))
        self.connect((self.blocks_selector_1_0, 0), (self.blocks_char_to_float_0, 0))
        self.connect((self.blocks_selector_1_0, 0), (self.blocks_repack_bits_bb_1, 0))
        self.connect((self.channels_channel_model_0, 0), (self.blocks_selector_0, 0))
        self.connect((self.digital_constellation_decoder_cb_0, 0), (self.blocks_selector_1_0, 1))
        self.connect((self.digital_constellation_decoder_cb_1, 0), (self.blocks_selector_1_0, 0))
        self.connect((self.digital_constellation_decoder_cb_1_0, 0), (self.blocks_selector_1_0, 5))
        self.connect((self.digital_constellation_decoder_cb_1_1, 0), (self.blocks_selector_1_0, 4))
        self.connect((self.digital_constellation_decoder_cb_1_2, 0), (self.blocks_selector_1_0, 2))
        self.connect((self.digital_constellation_decoder_cb_1_3, 0), (self.blocks_selector_1_0, 3))
        self.connect((self.digital_fll_band_edge_cc_0, 0), (self.blocks_selector_0, 1))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.blocks_selector_1, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.qtgui_const_sink_x_2_0, 0))
        self.connect((self.interp_fir_filter_xxx_1, 0), (self.blocks_multiply_const_vxx_0_0, 0))
        self.connect((self.soapy_rtlsdr_source_0, 0), (self.digital_fll_band_edge_cc_0, 0))
        self.connect((self.zeromq_pull_source_0, 0), (self.channels_channel_model_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "mqam_RX_TCP")
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
        self.qtgui_time_sink_x_1.set_samp_rate(self.symbol_rate)

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
        self.soapy_rtlsdr_source_0.set_sample_rate(0, self.samp_rate)

    def get_m_sel(self):
        return self.m_sel

    def set_m_sel(self, m_sel):
        self.m_sel = m_sel
        self.set_M([8, 16, 32, 64, 128, 256][self.m_sel])
        self._m_sel_callback(self.m_sel)
        self.blocks_selector_1.set_output_index(self.m_sel)
        self.blocks_selector_1_0.set_input_index(self.m_sel)

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
        self.blocks_multiply_const_vxx_0_0.set_k(1.0 / self.sps)
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

    def get_qam8_points(self):
        return self.qam8_points

    def set_qam8_points(self, qam8_points):
        self.qam8_points = qam8_points
        self.set_qam8_const(digital.constellation_calcdist(
            self.qam8_points,
            list(range(len(self.qam8_points))),
            1,
            1
        ).base())

    def get_qam64_points(self):
        return self.qam64_points

    def set_qam64_points(self, qam64_points):
        self.qam64_points = qam64_points
        self.set_qam64_const(digital.constellation_calcdist(
            self.qam64_points,
            list(range(len(self.qam64_points))),
            1,
            1
        ).base())

    def get_qam32_points(self):
        return self.qam32_points

    def set_qam32_points(self, qam32_points):
        self.qam32_points = qam32_points
        self.set_qam32_const(digital.constellation_calcdist(
            self.qam32_points,
            list(range(len(self.qam32_points))),
            1,
            1
        ).base())

    def get_qam256_points(self):
        return self.qam256_points

    def set_qam256_points(self, qam256_points):
        self.qam256_points = qam256_points
        self.set_qam256_const(digital.constellation_calcdist(
            self.qam256_points,
            list(range(len(self.qam256_points))),
            1,
            1
        ).base())

    def get_qam128_points(self):
        return self.qam128_points

    def set_qam128_points(self, qam128_points):
        self.qam128_points = qam128_points
        self.set_qam128_const(digital.constellation_calcdist(
            self.qam128_points,
            list(range(len(self.qam128_points))),
            1,
            1
        ).base())

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
        self.digital_symbol_sync_xx_0.set_ted_gain(self.ted_gain)

    def get_sample_phase(self):
        return self.sample_phase

    def set_sample_phase(self, sample_phase):
        self.sample_phase = sample_phase

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

    def get_qam8_const(self):
        return self.qam8_const

    def set_qam8_const(self, qam8_const):
        self.qam8_const = qam8_const
        self.digital_constellation_decoder_cb_1.set_constellation(self.qam8_const)

    def get_qam64_const(self):
        return self.qam64_const

    def set_qam64_const(self, qam64_const):
        self.qam64_const = qam64_const
        self.digital_constellation_decoder_cb_1_3.set_constellation(self.qam64_const)

    def get_qam32_const(self):
        return self.qam32_const

    def set_qam32_const(self, qam32_const):
        self.qam32_const = qam32_const
        self.digital_constellation_decoder_cb_1_2.set_constellation(self.qam32_const)

    def get_qam256_const(self):
        return self.qam256_const

    def set_qam256_const(self, qam256_const):
        self.qam256_const = qam256_const
        self.digital_constellation_decoder_cb_1_0.set_constellation(self.qam256_const)

    def get_qam128_const(self):
        return self.qam128_const

    def set_qam128_const(self, qam128_const):
        self.qam128_const = qam128_const
        self.digital_constellation_decoder_cb_1_1.set_constellation(self.qam128_const)

    def get_noise_voltage(self):
        return self.noise_voltage

    def set_noise_voltage(self, noise_voltage):
        self.noise_voltage = noise_voltage
        self.channels_channel_model_0.set_noise_voltage(self.noise_voltage)

    def get_medium(self):
        return self.medium

    def set_medium(self, medium):
        self.medium = medium
        self._medium_callback(self.medium)
        self.blocks_selector_0.set_input_index(self.medium)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.soapy_rtlsdr_source_0.set_frequency(0, self.freq)

    def get_bits_per_symbol(self):
        return self.bits_per_symbol

    def set_bits_per_symbol(self, bits_per_symbol):
        self.bits_per_symbol = bits_per_symbol
        self.blocks_repack_bits_bb_1.set_k_and_l(self.bits_per_symbol,8)

    def get_ber_window(self):
        return self.ber_window

    def set_ber_window(self, ber_window):
        self.ber_window = ber_window




def main(top_block_cls=mqam_RX_TCP, options=None):

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
