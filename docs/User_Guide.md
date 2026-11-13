# SCS Curve Number Reporting Toolbox: User Guide

## 1. Purpose

This guide explains how to prepare data, install the toolbox, generate an SCS Curve Number raster, and produce detailed reporting tables by watershed or subbasin.

The workflow extends standard Curve Number grid creation by preserving the underlying LULC and HSG combinations and reporting their areas and weighted contribution to the composite CN.

## 2. Software requirements

- ArcGIS Pro
- Spatial Analyst extension
- Permission to write to the selected output folder

## 3. Required inputs

### 3.1 Watershed or subbasin polygons

The input must be a polygon layer. Include a field that uniquely identifies each basin, such as `Basin`, `Basin_ID`, or `Subbasin`.

Recommended checks:

- No null Basin ID values
- One ID per subbasin
- No unintended polygon overlaps
- Projected coordinate system appropriate for the project

### 3.2 Land-use/land-cover raster

Use an integer categorical raster. NLCD is supported by the provided example lookup table.

Recommended preparation:

1. Clip or extract the raster to the watershed or a small buffer around it.
2. Project the raster to the project coordinate system.
3. Use **Nearest Neighbor** resampling.
4. Retain original integer land-cover codes.

### 3.3 Hydrologic Soil Group raster

The HSG raster must use:

| Value | HSG |
|---:|---|
| 1 | A |
| 2 | B |
| 3 | C |
| 4 | D |
| 5 | A/D |
| 6 | B/D |
| 7 | C/D |

The toolbox converts dual groups according to the selected drained/undrained parameter.

Recommended preparation:

- Use the same projection as the LULC raster.
- Retain integer categorical values.
- Check for NoData inside the watershed.

### 3.4 CN lookup table

The required fields are:

| Field | Purpose |
|---|---|
| `NLCD_CODE` | LULC code used for documentation |
| `LANDUSE` | Report description |
| `HSG_CODE` | 1=A, 2=B, 3=C, 4=D |
| `CN` | Curve Number |
| `JOIN_ID` | `NLCD_CODE x 10 + HSG_CODE` |

Use `lookup/CN_Lookup_Sample.xlsx` as a starting point. Import the `CN_Lookup` worksheet into a file geodatabase using **Excel To Table** before running the toolbox.

The sample values are examples from the USACE HEC-HMS tutorial. Modify them when required by an agency manual, approved project assumptions, hydrologic condition, or local land-use source.

## 4. Install the toolbox

1. Download the repository ZIP from GitHub.
2. Extract the ZIP to a local folder.
3. Open ArcGIS Pro.
4. In the Catalog pane, right-click **Toolboxes**.
5. Select **Add Toolbox**.
6. Browse to `SCS_CN_Reporting_Toolbox.pyt`.
7. Expand the toolbox and open **Generate Curve Number and Reports**.

## 5. Toolbox parameters

| Parameter | Description |
|---|---|
| Watershed or Subbasin Features | Polygon watershed/subbasin layer |
| Basin ID Field | User-selected field identifying basins |
| Land Use / Land Cover Raster | Integer categorical raster |
| Hydrologic Soil Group Raster | Integer HSG raster |
| Curve Number Lookup Table | Geodatabase table with `JOIN_ID`, `CN`, `LANDUSE` |
| Output Folder | Folder where the results geodatabase is created |
| Dual HSG Treatment | Drained or undrained treatment of values 5-7 |
| Output Name Prefix | Prefix used for the geodatabase and outputs |

## 6. Run the toolbox

1. Select the watershed layer.
2. Select the Basin ID field from the populated field dropdown.
3. Select the LULC raster.
4. Select the HSG raster.
5. Select the imported CN lookup table.
6. Select a writable output folder.
7. Choose the dual-HSG assumption.
8. Enter a unique output prefix.
9. Click **Run**.

Use a new prefix for repeated tests to avoid schema locks from open rasters or tables.

## 7. Processing performed by the toolbox

1. Sets the LULC raster as the snap raster and cell-size reference.
2. Limits processing extent and mask to the watershed polygons.
3. Reclassifies dual HSG values according to the selected assumption.
4. Combines LULC and HSG rasters while retaining both source values.
5. Calculates a numeric join key.
6. Joins the editable CN lookup table.
7. Creates the CN raster using the joined CN field.
8. Uses Tabulate Area to calculate each LULC-HSG combination within each basin.
9. Converts the wide area output into a long reporting table.
10. Calculates analyzed acreage and `CN x Area`.
11. Creates a clean detailed report.
12. Calculates the area-weighted composite CN for each basin.

## 8. Outputs

The selected output folder receives:

```text
<Prefix>_Results.gdb
```

### 8.1 CN raster

`<Prefix>_CN_Raster` stores the assigned Curve Number for every valid LULC-HSG cell.

### 8.2 Detailed report

`<Prefix>_Detailed_Report` contains one row per basin, HSG, land-use, and CN combination.

Key fields:

- Basin ID
- Soil Group
- Cover Description
- Curve Number
- Area (acres)
- CN x Area

### 8.3 Basin summary

`<Prefix>_Basin_Summary` contains:

- Basin ID
- Total analyzed raster area
- Total CN x Area
- Composite Curve Number

## 9. Quality control

### 9.1 Confirm lookup completeness

The tool stops when a LULC-HSG combination does not have a matching CN. Add the missing `JOIN_ID` to the lookup table and rerun.

### 9.2 Compare polygon and analyzed area

Raster areas may differ slightly from exact polygon areas because entire cells are assigned near boundaries. NoData in either raster also reduces analyzed area.

Calculate polygon acreage and compare it with the basin summary:

```text
Difference = Polygon Area - Analyzed Area
Coverage % = Analyzed Area / Polygon Area x 100
```

Suggested review thresholds:

- 98-100%: generally normal raster-boundary difference
- 95-98%: review NoData and boundary effects
- Below 95%: investigate missing LULC/HSG coverage before accepting results

Do not replace the analyzed-area denominator with the polygon area. Composite CN must remain based on cells with assigned CN values.

### 9.3 Review dual-HSG assumptions

- Drained option: A/D to A, B/D to B, C/D to C
- Undrained option: A/D, B/D, and C/D to D

Document the selected assumption in project files and reports.

## 10. Known limitations

- Raster resolution affects small basins and narrow features.
- NoData cells are excluded.
- NLCD does not directly identify detailed parcel uses such as commercial versus industrial.
- Lookup values require project/agency review.
- The tool does not determine whether dual-group soils are actually drained.
- Output is not survey-grade area measurement.

## 11. Troubleshooting

### Basin ID dropdown is blank

- Select the watershed layer first.
- Close and reopen the tool.
- Refresh or remove/re-add the `.pyt` toolbox if ArcGIS Pro cached an older parameter definition.

### Output already exists or is locked

- Close output tables and remove output rasters from the map.
- Use a new output prefix.

### Missing CN lookup match

- Open the combined raster table.
- Note the missing `JOIN_ID`.
- Add that combination to the lookup table and rerun.

### Unexpected area difference

- Compare polygon and analyzed areas.
- Inspect HSG and LULC NoData inside the basin.
- Confirm projection, cell size, and snap raster alignment.

## 12. References

- USACE HEC-HMS Curve Number Grid tutorial: https://www.hec.usace.army.mil/confluence/hmsdocs/hmsguides/gis-tools-and-terrain-data/gis-tutorials-and-guides/creating-a-curve-number-grid-and-computing-subbasin-average-curve-number-values
- ArcGIS Pro Combine: https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/combine.htm
- ArcGIS Pro Tabulate Area: https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/tabulate-area.htm
