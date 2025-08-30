# AerodromeUtilities

AerodromeUtilities is a simple plugin helping in fetching OSM data for airports, widening taxiways and exporting the data to data file formats of the [EuroScope](euroscope.hu/wp/) plugins [TopSky](https://forum.vatsim-scandinavia.org/d/38-topsky-plugin-25-beta-10) and [GroundRadar](https://forum.vatsim-scandinavia.org/d/33-ground-radar-plugin-15)

> **Note**: This plugin is still active development,if you find any bugs, you are more than welcome to report them by opening an issue.

## Quickstart

### **Install prerequisites**  
- QGIS (3.28+ recommended)  
- [QuickOSM plugin](https://plugins.qgis.org/plugins/QuickOSM/)  
- This plugin (download or install from ZIP) [here](https://plugins.qgis.org/plugins/widen-line-qgis-plugin)

### **Fetch airport data**  
  - Open the Processing Toolbox (`Ctrl+Alt+T`)  
   - Search for **Fetch Aerodrome Data**  
   - Enter an ICAO code (e.g. `HKJK`) and an output folder  
   - Run — your aerodrome layers will appear in QGIS.
### **Perform edits**
#### **Widen Txiways**
  - Recommended: set your **Project CRS** to `EPSG:3857` before widening (ensures buffer distance is in metres).  
  - The plugin attempts to convert CRS automatically, but `EPSG:3857` is the most reliable for widening. 
  - In the processing toolbox, select the taxiway widening algorithm.
  - **Input Layer**: Select the runway or taxiway layer you want to widen
  -  **Buffer Distance**: The total width of the taxiway
  - **Convert Polygon to Linestring**: Tick this if your are exporting using the old method, *this is not recommended, see [docs](https://github.com/BrakingChanges/widen-line-qgis-plugin/wiki)*
  - **Dissolve Result**: *Highly recommended* — smooths buffer ends to join taxiway section.
  - **Output Layer**: Set a file path to save the widened taxiway(*highly recommended*) or leave empty to set it to a temporary file  

#### **Adding text**
  - In order to add text data that the parser provided by this plugin can read, you need to create a layer of any type and add a string attribute named `TEXT`

#### **Adding Stand Information**
  - All attributes that are readable by the exporter parser in this plugin are in exact one-to-one concordance with GroundRadar `Stands.txt` file attributes, for example the `WTC` attribute states the intended aircraft weight class for that stands
  - Possible attributes are:
    - `STAND`: **Required** - The name of the stand
    - `WTC`: The intended weight class category of this stand
    - `USE`: The intended aircraft to be using the stand
    - `AREA`: Whether this stand is an indvidual stand or a widea area, like a GA apron.

#### **Manual Editing**
  - You may perform any number of operations to the polygons, linestrings and points within the QGIS project and they will be reflected in the final exported layout in EuroScope.
  - I recommend using Bing or Google Maps satellite imagery layers to correct for imperfections within the OSM data and align it to real world data
  - One example of manual editing is creating a line layer and drawing out the edges of runway markings using satellite data.

### **Exportation**
To export layers for EuroScope plugins:

1. Search for **Export Aerodrome Data** in the Processing Toolbox.
2. Enter:
   - **ICAO Code**
   - **Output Directory**
3. Run the tool, it will create three files:

| File              | Purpose                              |
|-------------------|--------------------------------------|
| `TopSkyMaps.txt`  | Map data for TopSky plugin           |
| `GroundRadar.txt` | Map data for GroundRadar plugin      |
| `Stands.txt`      | Stand data for GroundRadar plugin    |

---

### 🧩 Tips & Best Practices
- Always check OSM data visually: some airports may have missing or inaccurate geometry.
- For precise widening, compare with satellite imagery (Google, Bing, etc.).

More information on other algorithms in the [wiki](https://github.com/BrakingChanges/widen-line-qgis-plugin/wiki)

## Contribution
Contribution is always welcome, the current contribution process is as follows:
1. Fork the repo
2. Clone the repo
3. Checkout a branch from main
4. Make your changes
5. Push the changes
6. Make an issue with a supporting PR fixing that issues.


## 📄 License
GPL v2 or later — see [LICENSE](LICENSE).

---

**Links:**  
- [EuroScope](http://euroscope.hu/wp/)  
- [TopSky Plugin](https://forum.vatsim-scandinavia.org/d/38-topsky-plugin-25-beta-10)  
- [GroundRadar Plugin](https://forum.vatsim-scandinavia.org/d/33-ground-radar-plugin-15)  
- [QuickOSM Plugin](https://plugins.qgis.org/plugins/QuickOSM/)  

