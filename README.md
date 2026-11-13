# SCS Curve Number Reporting Toolbox for ArcGIS Pro

An ArcGIS Pro Python toolbox that creates a raster-based SCS Curve Number dataset and produces detailed land-use/hydrologic-soil-group reporting tables for each watershed or subbasin.

Unlike workflows that stop at the Curve Number raster, this toolbox also reports the land-use/HSG combinations, assigned CN values, analyzed acreage, weighted CN contribution, and composite CN by basin.

## Features

- Uses polygon watersheds or subbasins with a user-selected Basin ID field.
- Processes integer land-use/land-cover and hydrologic-soil-group rasters.
- Supports drained or undrained treatment of A/D, B/D, and C/D soil groups.
- Uses an editable external CN lookup table rather than hard-coded values.
- Creates a cell-by-cell Curve Number raster.
- Creates a detailed basin/LULC/HSG/CN/area report.
- Creates an area-weighted composite CN summary for each basin.
- Stores GIS outputs in a file geodatabase created in the selected output folder.

## Requirements

- ArcGIS Pro
- Spatial Analyst extension
- Integer LULC raster
- Integer HSG raster with codes 1=A, 2=B, 3=C, 4=D, 5=A/D, 6=B/D, 7=C/D
- Polygon watershed/subbasin layer with a Basin ID field
- CN lookup table containing `JOIN_ID`, `CN`, and `LANDUSE`

## Repository contents

```text
SCS-CN-Reporting-Toolbox/
├── SCS_CN_Reporting_Toolbox.pyt
├── README.md
├── CHANGELOG.md
├── LICENSE_TEMPLATE.txt
├── CITATION_TEMPLATE.cff
├── lookup/
│   └── CN_Lookup_Sample.xlsx
├── docs/
│   ├── User_Guide.md
│   └── images/
├── sample-data/
│   └── README.md
└── examples/
    └── README.md
```

## Installation

1. Download the repository using **Code > Download ZIP**, or download a tagged release from the **Releases** page.
2. Extract the ZIP to a local folder. Do not run the toolbox from inside the ZIP.
3. Open ArcGIS Pro.
4. Open the **Catalog** pane.
5. Right-click **Toolboxes** and choose **Add Toolbox**.
6. Browse to `SCS_CN_Reporting_Toolbox.pyt` and add it.
7. Expand the toolbox and open **Generate Curve Number and Reports**.

## Quick start

Provide these parameters:

1. **Watershed or Subbasin Features**: polygon feature layer.
2. **Basin ID Field**: field identifying each basin.
3. **Land Use / Land Cover Raster**: integer raster, such as NLCD.
4. **Hydrologic Soil Group Raster**: integer HSG raster.
5. **Curve Number Lookup Table**: imported geodatabase table based on `lookup/CN_Lookup_Sample.xlsx`.
6. **Output Folder**: normal folder where the results geodatabase will be created.
7. **Dual HSG Treatment**: drained or undrained assumption.
8. **Output Name Prefix**: unique prefix for the run.

Click **Run**.

## Main outputs

The tool creates `<Prefix>_Results.gdb` containing:

- `<Prefix>_CN_Raster`
- `<Prefix>_Detailed_Report`
- `<Prefix>_Basin_Summary`
- Supporting HSG, combined-raster, tabulate-area, and long-format datasets

### Detailed report fields

- Basin ID
- HSG
- Land use
- CN
- Area in acres
- CN x Area

### Basin summary fields

- Basin ID
- Total analyzed area
- Total CN x Area
- Composite CN

Composite CN is calculated as:

```text
Composite CN = Sum(CN x Area) / Sum(Analyzed Area)
```

## CN lookup table

`lookup/CN_Lookup_Sample.xlsx` contains an editable example crosswalk with:

```text
NLCD_CODE | LANDUSE | HSG_CODE | CN | JOIN_ID
```

where:

```text
JOIN_ID = NLCD_CODE x 10 + HSG_CODE
```

The sample values follow the example table in the USACE HEC-HMS curve-number-grid tutorial. They are examples, not universal design values. Review and modify the table to meet applicable agency and project requirements.

## Important limitations

- Raster-cell boundaries do not exactly match polygon boundaries. Small differences between polygon area and analyzed raster area are expected.
- Cells where either LULC or HSG is NoData are excluded from the combined raster and composite-CN calculation.
- Thirty-meter NLCD data may not represent small or detailed land-use features.
- NLCD developed-intensity classes are not identical to parcel-based commercial, industrial, or residential categories.
- Dual-HSG treatment must reflect documented drainage assumptions.
- The toolbox supports calculation and reporting but does not replace engineering review.

## Full documentation

See [docs/User_Guide.md](docs/User_Guide.md) for preparation, installation, execution, output interpretation, quality control, and troubleshooting.

## References

- USACE HEC-HMS, Creating a Curve Number Grid and Computing Subbasin Average Curve Number Values: https://www.hec.usace.army.mil/confluence/hmsdocs/hmsguides/gis-tools-and-terrain-data/gis-tutorials-and-guides/creating-a-curve-number-grid-and-computing-subbasin-average-curve-number-values
- ArcGIS Pro Combine: https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/combine.htm
- Example SCS Curve Number Generator repository: https://github.com/mohsennasab/SCS-Curve-Number-Generator-ArcGIS-Pro-Toolbox

## License and citation

Before publishing, replace `LICENSE_TEMPLATE.txt` and `CITATION_TEMPLATE.cff` with the selected license, author name, repository URL, and release details.
