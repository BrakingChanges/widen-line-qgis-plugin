import processing  # type:ignore
from qgis.PyQt.QtCore import QThread, pyqtSignal, QObject
from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer

class ExportWorker(QThread):
    """Handles export and file modification in a background thread."""
    finished = pyqtSignal()

    def __init__(self, iface, output_directory_path, icao_input_text, groundradar_file_path, topsky_file_path, stands_file_path, groundradar_line_number, topsky_line_number, stands_line_number):
        super().__init__()
        self.iface = iface
        self.output_directory_path = output_directory_path
        self.icao_input_text = icao_input_text
        self.groundradar_file_path = groundradar_file_path
        self.topsky_file_path = topsky_file_path
        self.stands_file_path = stands_file_path
        self.groundradar_line_number = groundradar_line_number
        self.topsky_line_number = topsky_line_number
        self.stands_line_number = stands_line_number

    def run(self):
        """Runs the processing algorithm and modifies files in a separate thread."""
        
        processing.run("aerodromeutilities:geojsontotopskygroundradar", {
            "OUT_DIR": self.output_directory_path,
            "ICAO": self.icao_input_text,
            "MULTI_MAP": False,
        })
        
        self.modify_file()
        self.finished.emit()  # Signal that processing is done

    def modify_file(self):
        """Handles file modifications after processing."""
        for file_name, file_path, line_number in [
            ("GroundRadar.txt", self.groundradar_file_path, self.groundradar_line_number),
            ("TopSkyMaps.txt", self.topsky_file_path, self.topsky_line_number),
            ("Stands.txt", self.stands_file_path, self.stands_line_number),
        ]:
            # Read the newly exported data
            with open(f'{self.output_directory_path}/{file_name}', 'r') as output_file:
                new_output = output_file.read().strip()  # Strip to avoid unwanted blank lines

            # Read the existing file
            with open(file_path, 'r+') as file:
                lines = file.readlines()

                # Find where the previous version starts and ends
                start = line_number
                end = start
                while end < len(lines) and lines[end].strip():  
                    end += 1  # Move until an empty line or end of file

                # Replace the old version with the new one
                updated_lines = lines[:start] + [new_output + "\n"] + lines[end:]

                # Write back the modified content
                file.seek(0)
                file.writelines(updated_lines)
                file.truncate()


class Debugger:
    """Handles layer watching in a background thread."""
    def __init__(self):
        super().__init__()
        self.iface = None
        self.output_directory_path = None
        self.icao_input_text = None
        self.groundradar_file_path = None
        self.topsky_file_path = None
        self.stands_file_path = None
        self.groundradar_line_number = None
        self.topsky_line_number = None
        self.stands_line_number = None
        self.worker_thread = None

    def run(self, iface, output_directory_path, icao_input_text, groundradar_file_path, topsky_file_path, stands_file_path, groundradar_line_number, topsky_line_number, stands_line_number):
        self.iface = iface
        self.output_directory_path = output_directory_path
        self.icao_input_text = icao_input_text
        self.groundradar_file_path = groundradar_file_path
        self.topsky_file_path = topsky_file_path
        self.stands_file_path = stands_file_path
        self.groundradar_line_number = groundradar_line_number
        self.topsky_line_number = topsky_line_number
        self.stands_line_number = stands_line_number
        
        """Thread execution: watches layer changes and triggers recompile."""
        QgsProject.instance().layersAdded.connect(self.on_layers_added)
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                self.connect_layer_signals(layer)

    def stop(self):
        """Stops the thread safely."""
        QgsProject.instance().layersAdded.disconnect(self.on_layers_added)
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                self.disconnect_layer_signals(layer)

    def on_layers_added(self, layers):
        """Attach signals to new layers when they are added."""
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                self.connect_layer_signals(layer)

    def on_features_added(self, layer, feature_ids):
        self.recompile()

    def on_features_removed(self, layer, feature_ids):
        self.recompile()

    def on_attributes_changed(self, layer, changes):
        self.recompile()

    def on_layer_modified(self, layer):
        self.recompile()

    def recompile(self):
        """Runs the export and file modifications in a separate thread."""
        if self.worker_thread and self.worker_thread.isRunning():
            return  # Prevent multiple concurrent threads
        
        self.worker_thread = ExportWorker(
            self.iface, self.output_directory_path, self.icao_input_text,
            self.groundradar_file_path, self.topsky_file_path, self.stands_file_path,
            self.groundradar_line_number, self.topsky_line_number, self.stands_line_number
        )
        
        self.worker_thread.finished.connect(self.on_export_finished)
        self.worker_thread.start()

    def on_export_finished(self):
        """Handles post-processing UI update."""
        self.iface.messageBar().pushMessage("Files Modified", "Export complete.", level=0)

    def connect_layer_signals(self, layer):
        """Connect signals for the given layer."""
        layer.committedFeaturesAdded.connect(lambda fid: self.on_features_added(layer, fid))
        layer.committedFeaturesRemoved.connect(lambda fid: self.on_features_removed(layer, fid))
        layer.committedAttributeValuesChanges.connect(lambda fid, changes: self.on_attributes_changed(layer, changes))
        layer.layerModified.connect(lambda: self.on_layer_modified(layer))

    def disconnect_layer_signals(self, layer):
        """Disconnect signals for the given layer."""
        layer.committedFeaturesAdded.disconnect()
        layer.committedFeaturesRemoved.disconnect()
        layer.committedAttributeValuesChanges.disconnect()
        layer.layerModified.disconnect()
