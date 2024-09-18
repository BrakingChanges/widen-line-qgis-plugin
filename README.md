# TaxiwayWidener(AerodromeUtilities)

TaxiwayWidener, now AerodromeUtilities is a simple plugin helping in fetching OSM data for airports, widening taxiways and converting polygons to linestring. **PLEASE NOTE: This plugin is quite incomplete :) so except many bugs**

## Fetching Airport OSM Data
![Fetching OSM Data](osmfetcher.png)
To fetch OSM Data, you can access it via the processing toolbox by settings cog icon in QGis toolbar or `Ctrl+Alt+T`. Next, you can set an ICAO Code and setting an output folder. I reccommend adding it to a folder like `{ICAO}/Step 1`. When you click "Run", different layers should be loaded and you should see them being generated on the map. At the end of the execution, you might see layers failing to generate like this:
![OSM Normal Red Text](osmfetchererror.png)
This message is normal so it is safe to ignore. *I haven't yet found the cause of this.*

## Widening Taxiways / Runways
With the airport loaded, you can select the taxiwaywidener tool from the processing tool under AerodromeUtilities. When you select the tool, the following interface will pop up.
![alt text](image.png)
  
Options
- Input Layer: This is the input line layer you want to widen (eg taxiway/runway layer)
- Buffer distance: The distance you want to extend each side by(**not the taxiway/runway witdth but it divided by 2**)
- Convert Polygon to linestring: Whether to convert the resultant polygon back into a linestring for export to TS/GR 
- Dissolve Result: Smooths the end caps generated by the native buffer tool in QGis. *Highly reccommended because it reduces the risk of TS Not accepting it as a plygon*
- Output Layer - Saves the output layer to a file which is reccommended to prevent losing any layer

### Fixing the CRS
After running the algorithm, you will not see any layer showing up. This is because, running the algorithm will remove the CRS status from the project from some reason, causing all new layers to not show up.

To fix this, click the Project CRS button(highlighted green below) and a prompt will show up
![Project CRS Button](image-1.png)

In this window, it should say that there is no CRS selected, uncheck that box then select WGS 84. After that, you can click Ok, to set the new project CRS.
![Setting Project CRS](image-2.png)

Then taxiways should show up as configured!
![Project CRS Done](image-3.png)