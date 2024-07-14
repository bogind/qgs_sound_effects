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
import os
from qgis.PyQt.QtCore import QCoreApplication, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from qgis.core import (QgsProcessingProvider, QgsProcessingAlgorithm, 
                        QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum)

from qgis.PyQt.QtGui import QIcon


class PlaySoundAlgorithm(QgsProcessingAlgorithm):
    
    
    SOUND = 'SOUND'
    VOLUME = 'VOLUME'
    LOOPS_ENABLED = 'LOOPS_ENABLED'
    LOOPS = 'LOOPS'
    OUTPUT = 'OUTPUT'
    

    @staticmethod
    def name():
        return 'play_sound'
    
    @staticmethod
    def displayName():
        return 'Play Sound'
    
    @staticmethod
    def group() -> str:
        """Return the group of the algorithm."""
        return ''

    @staticmethod
    def groupId() -> str:
        """Return the id of the group."""
        return ''
    
    @staticmethod
    def shortHelpString():
        return 'Play a sound effect'
    
    def icon(self):
        return QIcon(':/plugins/qgs_sound_effects/qgs_effects_icon.png')
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
    
    def initAlgorithm(self, config):
        self.plugin_dir = os.path.dirname(__file__)
        self.sounds_config = json.load(open(os.path.join(self.plugin_dir,'sounds.json')))
        self.sound_names = [self.sounds_config[s]['label'] for s in self.sounds_config.keys()]

        sound_param = QgsProcessingParameterEnum(
                self.SOUND,
                self.tr('Sound'),
                options=self.sound_names,
                defaultValue=self.sound_names[0]
            )
        volume_param = QgsProcessingParameterNumber(
                self.VOLUME,
                self.tr('Volume'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                defaultValue=1.0,
                maxValue=1.0,
                minValue=0.0
            )
        params = [sound_param, volume_param]
        for param in params:
            self.addParameter(param)

    def processAlgorithm(self, parameters, context, feedback):
        try:
            #sound = parameters[self.SOUND]
            sound = self.parameterAsEnum(parameters, self.SOUND, context)
            volume = self.parameterAsDouble(parameters, self.VOLUME, context)

            keys = self.sounds_config.keys()
            sound = self.sounds_config[list(keys)[sound]]
            file_path = os.path.join(self.plugin_dir, sound['filename'])

            feedback.pushInfo('Playing sound effect: {} at volume {}'.format(sound['label'], volume))

            self.player = QMediaPlayer()
            self.player.setVolume(int(volume*100))
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.player.play()


        except Exception as e:
            print(e)
            return {self.OUTPUT: 'Failed to play sound effect'}


        return {self.OUTPUT:{
            'SOUND': sound['label'], 
            'VOLUME': volume, 
            'OUTPUT': 'Played Sound Effect'}
            }
    

    def createInstance(self):
        return PlaySoundAlgorithm()
    


class QgisSoundEffectsProvider(QgsProcessingProvider):
    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def id(self):
        return 'qgis_sound_effects'
    
    def name(self):
        return self.tr('QGIS Sound Effects')
    
    def icon(self):
        return QIcon(':/plugins/qgs_sound_effects/qgs_effects_icon.png')
    
    def unload(self):
        pass
    
    def loadAlgorithms(self):
        self.addAlgorithm(PlaySoundAlgorithm())
    