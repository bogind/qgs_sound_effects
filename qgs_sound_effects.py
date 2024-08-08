# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisSoundEffects
                                 A QGIS plugin
 Add sound effects to QGIS to make work less boring
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-07-07
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Dror Bogin
        email                : dror.bogin@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import json
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QTimer, QDateTime, QUrl, QMetaMethod
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QCheckBox, QToolButton, QComboBox, QDoubleSpinBox
from qgis.gui import QgsGui
from qgis.core import QgsSettings, QgsApplication, QgsMessageLog, Qgis
from PyQt5.QtMultimedia import QSoundEffect

# Initialize Qt resources from file resources.py
from .resources import *  # noqa: F403
from .qgs_sound_effects_provider import QgisSoundEffectsProvider
# Import the code for the dialog
from .qgs_sound_effects_dialog import QgisSoundEffectsDialog, QgisSoundEffectsConfigDialog
import os.path

MESSAGE_CATEGORY = 'QGIS Sound Effects'

class QgisSoundEffects:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # Save reference to the QGIS message bar
        self.mb = self.iface.messageBar()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QgisSoundEffects_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.config_window = None
        self.provider = None
        self.last_entry = None
        self.actions = []
        self.previousScale = self.iface.mapCanvas().scale()
        self.taskManager = QgsApplication.taskManager()
        self.config = self.restore_settings()
        self.menu = self.tr(u'&QGIS Sound Effects')
        with open(os.path.join(self.plugin_dir,'sounds.json')) as f:
            self.sounds_config = json.load(f)
            f.close()

        self.sound_names = [self.sounds_config[s]['label'] for s in self.sounds_config.keys()]
        self.sound_effects = {}
        for sound in self.sounds_config.keys():
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(os.path.join(self.plugin_dir, self.sounds_config[sound]['filename'])))
            self.sound_effects[sound] = effect

        

        self.canvas_events = {
            'scale_changed': {
                'id': 'scaleChanged',
                'sound': 'success',
                'enabled': True,
            },
            'layers_changed': {
                'id': 'layersChanged',
                'sound': 'success',
                'enabled': True,
            },
            'render_complete': {
                'id': 'renderComplete',
                'sound': 'success',
                'enabled': True,

            },
            'render_error': {
                'id': 'renderErrorOccurred',
                'sound': 'fail',
                'enabled': True,
            }
            
        }
        self.history = QgsGui.historyProviderRegistry()
        self.configure()
        self.update_last_entry()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_processing_entry)
        self.timer.start(1000)

        
        #self.history.entryAdded.connect(self.onEntryAdded)

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QgisSoundEffects', message)
    
    def configure(self):
        """Configure the plugin"""
        try:
            if self.config is None:
                self.config = self.restore_settings()
            if self.previousScale is None:
                self.previousScale = self.iface.mapCanvas().scale()
            self.bound_sounds = {
                'processingFailure': QSoundEffect(),
                'processingSuccess': QSoundEffect(),
                'zoomIn': QSoundEffect(),
                'zoomOut': QSoundEffect(),
                'layersChanged': QSoundEffect(),
                'renderComplete': QSoundEffect(),
                'renderErrorOccurred': QSoundEffect(),
                'mapExportComplete': QSoundEffect(),
                'mapExportError': QSoundEffect(),
                'printLayoutExportSuccess': QSoundEffect(),
            }
            for event in self.bound_sounds.keys():
                eventConfig = self.config.get(event, {})
                soundID = eventConfig.get('sound', 'success')
                volume = eventConfig.get('volume', 1.0)
                self.bound_sounds[event].setSource(self.sound_effects[soundID].source())
                self.bound_sounds[event].setVolume(volume)
        except Exception as e:
            self.mb.pushCritical('Error configuring sound effects plugin', str(e))

        self.toggle_canvas_events()
        self.toggle_export_events()
        
    
    def toggle_canvas_events(self):
        # Check if all events are enabled
        if self.enabled is True:
            config  = self.config.get('layersChanged', {})
            enabled = config.get('enabled', False)

            # Check if the layersChanged event is enabled
            if enabled is True:
                self.iface.mapCanvas().layersChanged.connect(self.bound_sounds['layersChanged'].play)
            else:
                try:
                    self.iface.mapCanvas().layersChanged.disconnect(self.bound_sounds['layersChanged'].play)
                except Exception as e: # noqa: F841
                    # This will happen if the event was not connected
                    pass

            zoomInconfig  = self.config.get('zoomIn', {})
            zoomOutconfig  = self.config.get('zoomOut', {})
            zoomInEnabled = zoomInconfig.get('enabled', False)
            zoomOutEnabled = zoomOutconfig.get('enabled', False)
            
            # Check if the zoomIn or zoomOut events are enabled
            if zoomInEnabled is True or zoomOutEnabled is True:
                self.iface.mapCanvas().scaleChanged.connect(self.onScaleChanged)
            else:
                try:
                    self.iface.mapCanvas().scaleChanged.disconnect(self.onScaleChanged)
                except Exception as e:  # noqa: F841
                    # This will happen if the event was not connected
                    pass

            if zoomInEnabled is False and zoomOutEnabled is False:
                self.previousScale = self.iface.mapCanvas().scale()
                try:
                    self.iface.mapCanvas().scaleChanged.disconnect(self.onScaleChanged)
                except Exception as e:  # noqa: F841
                    # This will happen if the event was not connected
                    pass
                    
            config  = self.config.get('renderComplete', {})
            enabled = config.get('enabled', False)
            # Check if the renderComplete event is enabled
            if enabled is True:
                self.iface.mapCanvas().renderComplete.connect(self.bound_sounds['renderComplete'].play)
            else:
                try:
                    self.iface.mapCanvas().renderComplete.disconnect(self.bound_sounds['renderComplete'].play)
                except Exception as e: # noqa: F841
                    # This will happen if the event was not connected
                    pass         

            config  = self.config.get('renderErrorOccurred', {})
            enabled = config.get('enabled', False)
            # Check if the renderErrorOccurred event is enabled
            if enabled is True:
                self.iface.mapCanvas().renderErrorOccurred.connect(self.bound_sounds['renderErrorOccurred'].play)
            else:
                try:
                    self.iface.mapCanvas().renderErrorOccurred.disconnect(self.bound_sounds['renderErrorOccurred'].play)
                except Exception as e: # noqa: F841
                    # This will happen if the event was not connected
                    pass
        else:
            # Disable all events when the plugin is disabled
            try:
                self.iface.mapCanvas().layersChanged.disconnect(self.bound_sounds['layersChanged'].play)
                self.iface.mapCanvas().scaleChanged.disconnect(self.onScaleChanged)
                self.iface.mapCanvas().renderComplete.disconnect(self.bound_sounds['renderComplete'].play)
                self.iface.mapCanvas().renderErrorOccurred.disconnect(self.bound_sounds['renderErrorOccurred'].play)
            except Exception as e: # noqa: F841
                # This will happen if the event was not connected
                pass

    def toggle_export_events(self):
        try:
            if self.enabled is True:
                # print layout export success
                config  = self.config.get('printLayoutExportSuccess', {})
                enabled = config.get('enabled', False)
                if enabled is True:
                    self.iface.layoutDesignerOpened.connect(self.attachLayoutDesignerExportSuccessListener)
                else:
                    self.iface.layoutDesignerOpened.connect(self.disconnectLayoutDesignerExportSuccessListener)

                # map export complete
                config  = self.config.get('mapExportComplete', {})
                enabled = config.get('enabled', False)
                if enabled is True:
                    self.taskManager.taskAdded.connect(self.mapExportSuccessTaskListener)
                else:
                    try:
                        self.taskManager.taskAdded.disconnect(self.mapExportSuccessTaskListener)
                    except Exception as e: # noqa: F841
                        # This will happen if the event was not connected
                        pass

                # map export error
                config  = self.config.get('mapExportError', {})
                enabled = config.get('enabled', False)
                if enabled is True:
                    self.taskManager.taskAdded.connect(self.mapExportErrorTaskListener)
                else:
                    try:
                        self.taskManager.taskAdded.disconnect(self.mapExportErrorTaskListener)
                    except Exception as e: # noqa: F841
                        # This will happen if the event was not connected
                        pass

            else:
                pass
        except Exception as e:
            self.mb.pushCritical('Error toggling export events', str(e))
            QgsMessageLog.logMessage('Error toggling export events: {}'.format(e), MESSAGE_CATEGORY, Qgis.Critical)
            QgsMessageLog.logMessage(str(e.__traceback__), MESSAGE_CATEGORY, Qgis.Critical)

    
    def attachLayoutDesignerExportSuccessListener(self, designer):
        designer.layoutExported.connect(self.bound_sounds['printLayoutExportSuccess'].play)

    def disconnectLayoutDesignerExportSuccessListener(self, designer):
        try:
            designer.layoutExported.disconnect(self.bound_sounds['printLayoutExportSuccess'].play)
        except Exception as e: # noqa: F841
            # This will happen if the event was not connected
            pass
        try:
            self.iface.layoutDesignerOpened.disconnect(self.disconnectLayoutDesignerExportSuccessListener)
        except Exception as e: # noqa: F841
            # This will happen if the event was not connected
            pass

    def mapExportSuccessTaskListener(self, taskId):
        task = self.taskManager.task(taskId)
        if(self.iface.tr("Saving as image") == task.description() or self.iface.tr("Saving as PDF") == task.description()):
            #task.taskCompleted.connect(self.bound_sounds['mapExportComplete'].play)
            for i in range (task.metaObject().methodCount()):
                method = task.metaObject().method(i)
                if not method.isValid():
                    continue
                if method.methodType() == QMetaMethod.Signal:
                    if method.name() == 'renderingComplete':
                        task.renderingComplete.connect(self.bound_sounds['mapExportComplete'].play)
        else:
            pass

    def mapExportErrorTaskListener(self, taskId):
        task = self.taskManager.task(taskId)
        if(self.iface.tr("Saving as image") == task.description() or self.iface.tr("Saving as PDF") == task.description()):
            for i in range (task.metaObject().methodCount()):
                method = task.metaObject().method(i)
                if not method.isValid():
                    continue
                if method.methodType() == QMetaMethod.Signal:
                    if method.name() == 'errorOccurred':
                        task.errorOccurred.connect(self.bound_sounds['mapExportError'].play)
        else:
            pass


    def onScaleChanged(self, scale): 
        previousScale = self.previousScale
        zoomInconfig  = self.config.get('zoomIn', {})
        zoomOutconfig  = self.config.get('zoomOut', {})
        zoomInEnabled = zoomInconfig.get('enabled', False)
        zoomOutEnabled = zoomOutconfig.get('enabled', False)      
        if self.enabled is True: 
            if self.previousScale is None:
                pass
            else:
                if previousScale > scale:
                    if zoomInEnabled is True:
                        self.bound_sounds['zoomIn'].play()
                elif previousScale < scale:
                    if zoomOutEnabled is True:
                        self.bound_sounds['zoomOut'].play()
                else:
                    # Happens when window is resized, QGIS retains scale
                    pass
        
        self.previousScale = scale


    def update_last_entry(self):
        """Update the last entry id on plugin init"""
        try:
            history = QgsGui.historyProviderRegistry()
            entries = history.queryEntries()
            if len(entries) == 0:
                return
            self.last_entry = entries[len(entries)-1].id
        except Exception as e:
            self.mb.pushCritical('Error updating last entry on init', str(e))


    def check_processing_entry(self):
        """Check if the processing entry succeeded or failed"""
        try:
            
            processingSuccessConfig  = self.config.get('processingSuccess', {})
            processingFailureConfig  = self.config.get('processingFailure', {})
            processingSuccessEnabled = processingSuccessConfig.get('enabled', False)
            processingFailureEnabled = processingFailureConfig.get('enabled', False) 

            # Check only the last second
            entries = self.history.queryEntries(QDateTime.currentDateTime().addSecs(-1),QDateTime.currentDateTime())
            if len(entries) == 0:
                return
            last_entry = entries[len(entries)-1]
            if(self.last_entry == last_entry.id):
                return
            
            if last_entry is None:
                return # No entries, should not happen
            if 'results' in last_entry.entry:
                if last_entry.entry['results'] is None:
                    if processingFailureEnabled:
                        self.bound_sounds['processingFailure'].play()
                else:
                    if processingSuccessEnabled:
                        self.bound_sounds['processingSuccess'].play()

            # Update the last entry id
            self.lastEntry = last_entry.id
        except Exception as e:
            self.mb.pushCritical('Error checking processing entry', str(e))

    def play_sound(self, sound):
        #self.sounds[sound]['sound'].play()
        self.sound_effects[sound].play()


    def initProcessing(self):
        self.provider = QgisSoundEffectsProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.initProcessing()

        icon_path = ':/plugins/qgs_sound_effects/qgs_effects_icon.png'
        config_icon_path = ':/plugins/qgs_sound_effects/qgs_effects_config_icon.png'
        
        # Add the toolbar
        self.toolbar = self.iface.addToolBar('Sound Effects Toolbar')
        self.toolbar.setObjectName('Sound Effects')

        # Add Icon
        self.icon = QIcon(icon_path)

        # Add the sound effects toggle
        self.sound_effects_toggle = QCheckBox('Enable Sound Effects')
        self.sound_effects_toggle.setIcon(self.icon) 
        sound_effects_enabled = self.get_setting('enabled', True)
        if sound_effects_enabled:
            self.sound_effects_toggle.setChecked(True)
        if type(sound_effects_enabled) is str:
            if sound_effects_enabled.lower() == 'true':
                self.sound_effects_toggle.setChecked(True)
                self.enabled = True
            else:
                self.sound_effects_toggle.setChecked(False)
                self.enabled = False
        self.sound_effects_toggle.stateChanged.connect(self.toggle_sound_effects)
        self.toggle_sound_effects()

        # Add the sound effects toggle to the toolbar
        self.toolbar.addWidget(self.sound_effects_toggle)

        #self.create_settings_window()
        self.config_window = QgisSoundEffectsConfigDialog()

        # Add the configuration icon
        self.config_icon = QIcon(config_icon_path)
        self.config_action = QAction(self.config_icon, 'Configure Sound Effects', self.iface.mainWindow())
        self.config_action.triggered.connect(self.show_settings)

        self.configure_settings_window()

        self.toolbar.addAction(self.config_action)

        # will be set False in run()
        self.first_start = True


        
    def configure_settings_window(self):
        self.checkbox_ids = ['processingSuccessCheckBox', 'processingFailureCheckBox', 'zoomInCheckBox',
                        'zoomOutCheckBox','layersChangedCheckBox','renderCompleteCheckBox','renderErrorOccurredCheckBox',
                        'mapExportCompleteCheckBox','mapExportErrorCheckBox','printLayoutExportSuccessCheckBox']
        self.combobox_ids = ['processingSuccessComboBox','processingFailureComboBox','zoomInComboBox',
                        'zoomOutComboBox','layersChangedComboBox','renderCompleteComboBox','renderErrorOccurredComboBox',
                        'mapExportCompleteComboBox','mapExportErrorComboBox','printLayoutExportSuccessComboBox']
        self.test_button_ids = ['processingSuccessTestButton','processingFailureTestButton','zoomInTestButton',
                        'zoomOutTestButton','layersChangedTestButton','renderCompleteTestButton','renderErrorOccurredTestButton',
                        'mapExportCompleteTestButton','mapExportErrorTestButton','printLayoutExportSuccessTestButton']
        self.volume_ids = ['processingSuccessVolume','processingFailureVolume','zoomInVolume',
                        'zoomOutVolume','layersChangedVolume','renderCompleteVolume','renderErrorOccurredVolume',
                        'mapExportCompleteVolume','mapExportErrorVolume','printLayoutExportSuccessVolume']
        
        
        for i in range(0, len(self.checkbox_ids)):
            eventID = self.objectid_to_eventid(self.checkbox_ids[i])
            eventConfig = self.config.get(eventID, {})

            checkbox_id = self.checkbox_ids[i]
            checkbox = self.config_window.findChild(QCheckBox, checkbox_id)
            checked = eventConfig.get('enabled', False)
            checkbox.setChecked(checked)
            checkbox.stateChanged.connect(self.make_toggle_event(checkbox_id))

            combobox_id = self.combobox_ids[i]
            comboBox = self.config_window.findChild(QComboBox, combobox_id)
            for j in self.sounds_config.keys():
                comboBox.addItem(self.sounds_config[j]['label'], j)

            eventSoundIndex = eventConfig.get('sound_index', 0)
            
            comboBox.setCurrentIndex(eventSoundIndex)
            comboBox.currentIndexChanged.connect(self.make_set_event_sound(combobox_id))
            
            test_button_id = self.test_button_ids[i]
            test_button = self.config_window.findChild(QToolButton, test_button_id)
            test_button.clicked.connect(self.make_test_sound(combobox_id))

            volume_id = self.volume_ids[i]
            volume = self.config_window.findChild(QDoubleSpinBox, volume_id)
            configVolume = eventConfig.get('volume', 1.0)
            volume.setValue(configVolume)

        self.config_window.saveSettingsButton.clicked.connect(self.save_settings)
        self.config_window.cancelChangesButton.clicked.connect(self.config_window.hide)

    def make_set_event_sound(self, id):
        def set_event_sound():
            pass
        return set_event_sound
    
    def make_test_sound(self, id):
        def test_sound():
            comboBox = self.config_window.findChild(QComboBox, id)
            self.play_sound(comboBox.currentData())
        return test_sound
    
    def make_toggle_event(self, id):
        def toggle_event(state):
            state = state == 2
            checkbox = self.config_window.findChild(QCheckBox, id)
            checkbox.setChecked(state)
    
        return toggle_event
    
    @staticmethod
    def objectid_to_eventid(objid):
        return objid.replace('CheckBox','').replace('ComboBox','').replace('TestButton','').replace('Volume','')
    

    def restore_settings(self):
        try:
            self.enabled = self.get_setting('enabled', True)
            default_config = '{"layersChanged": {"enabled": false, "sound": "woodenfrog", "sound_index": 10, "volume": 1.0}, "processingFailure": {"enabled": true, "sound": "fail", "sound_index": 0, "volume": 1.0}, "processingSuccess": {"enabled": true, "sound": "success", "sound_index": 1, "volume": 1.0}, "renderComplete": {"enabled": false, "sound": "fail", "sound_index": 0, "volume": 1.0}, "renderErrorOccurred": {"enabled": false, "sound": "fail", "sound_index": 0, "volume": 1.0}, "zoomIn": {"enabled": false, "sound": "synth-glide", "sound_index": 6, "volume": 1.0}, "zoomOut": {"enabled": false, "sound": "synth-glide", "sound_index": 6, "volume": 1.0}, "mapExportComplete": {"enabled": false, "sound": "good_answer_harp", "sound_index": 12, "volume": 1.0}, "mapExportError": {"enabled": false, "sound": "sad_trombone", "sound_index": 14, "volume": 1.0}, "printLayoutExportSuccess": {"enabled": false, "sound": "tada", "sound_index": 13, "volume": 1.0}}'
            config = json.loads(self.get_setting('config', default_config))
            return config
        except Exception as e:
            QgsMessageLog.logMessage('Error restoring settings: {}'.format(str(e)), MESSAGE_CATEGORY, Qgis.Critical)
            return {}
    

    def save_settings(self):
        try:
            for i in range(0, len(self.checkbox_ids)):
                eventID = self.objectid_to_eventid(self.checkbox_ids[i])
                
                checkbox_id = self.checkbox_ids[i]
                checkbox = self.config_window.findChild(QCheckBox, checkbox_id)
                checked = checkbox.isChecked()
                
                combobox_id = self.combobox_ids[i]
                comboBox = self.config_window.findChild(QComboBox, combobox_id)
                
                

                volume_id = self.volume_ids[i]
                volume = self.config_window.findChild(QDoubleSpinBox, volume_id)
                
                event = {
                    'enabled': checked,
                    'sound': comboBox.currentData(),
                    'sound_index': comboBox.currentIndex(),
                    'volume': volume.value()
                }
                self.config[eventID] = event
                
            self.set_setting('config', json.dumps(self.config))
            self.configure()
        except Exception as e:
            QgsMessageLog.logMessage('Error saving settings: {}'.format(str(e)), MESSAGE_CATEGORY, Qgis.Critical)
            
        self.config_window.hide()


    def show_settings(self):
        """Show the settings dialog"""
        self.config_window.show()


    def get_setting(self, key: str, default: str = None):
        """Get a value in the QgsSettings.

        :param key: The key to fetch in the QgsSettings
        :type key: basestring

        :param default: The default value if the key is not found.
        :type default: basestring

        :return: The value or the default value.
        :rtype: basestring
        """
        q_setting = QgsSettings()
        prefix = '/QgisSoundEffects/'
        value = q_setting.value(prefix + key)

        if value is not None:
            return value

        return default


    def set_setting(self, key: str, value: str):
        """
        Set a value in the QgsSettings
        :param key: key
        :type key: str

        :param value: value
        :type value: str

        :return: result
        :rtype: bool
        """
        q_setting = QgsSettings()
        prefix = '/QgisSoundEffects/'
        return q_setting.setValue(prefix + key, value)
    

    def toggle_sound_effects(self):
        """Toggle sound effects on and off"""
        self.enabled = self.sound_effects_toggle.isChecked()
        self.set_setting('enabled', self.enabled)
        self.update_last_entry()
        self.toggle_canvas_events()
        self.toggle_export_events()
        if self.enabled is True:
            self.timer.start(1000)            
        else:
            self.timer.stop()


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.timer.stop()
        # remove the toolbar
        if self.toolbar is not None:
            self.toolbar = None
        
        provider = QgsApplication.processingRegistry().providerById(self.provider.id())
        if provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start is True:
            self.first_start = False
            # No dialog yet, should be used for configuration of sounds to events
            self.dlg = QgisSoundEffectsDialog()            

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
