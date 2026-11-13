# -*- coding: utf-8 -*-

import arcpy
import os


class Toolbox:
    def __init__(self):
        self.label = "SCS Curve Number Reporting Toolbox"
        self.alias = "scscnreporting"
        self.tools = [GenerateCurveNumberReports]


class GenerateCurveNumberReports:
    def __init__(self):
        self.label = "Generate Curve Number and Reports"
        self.description = (
            "Creates an SCS curve number raster, detailed land-use and "
            "hydrologic-soil-group area table, and composite CN summary by basin."
        )

    def getParameterInfo(self):
        watershed = arcpy.Parameter(
            displayName="Watershed or Subbasin Features",
            name="watershed_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        watershed.filter.list = ["Polygon"]

        basin_field = arcpy.Parameter(
            displayName="Basin ID Field",
            name="basin_id_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        basin_field.parameterDependencies = [watershed.name]

        lulc_raster = arcpy.Parameter(
            displayName="Land Use / Land Cover Raster",
            name="lulc_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )

        hsg_raster = arcpy.Parameter(
            displayName="Hydrologic Soil Group Raster",
            name="hsg_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )

        cn_lookup = arcpy.Parameter(
            displayName="Curve Number Lookup Table",
            name="cn_lookup_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input"
        )

        output_folder = arcpy.Parameter(
            displayName="Output Folder",
            name="output_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )

        dual_hsg = arcpy.Parameter(
            displayName="Dual HSG Treatment",
            name="dual_hsg_treatment",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        dual_hsg.filter.type = "ValueList"
        dual_hsg.filter.list = [
            "Drained: A/D to A, B/D to B, C/D to C",
            "Undrained: A/D to D, B/D to D, C/D to D"
        ]
        dual_hsg.value = "Drained: A/D to A, B/D to B, C/D to C"

        output_prefix = arcpy.Parameter(
            displayName="Output Name Prefix",
            name="output_prefix",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        output_prefix.value = "SCS_CN"

        cn_raster_output = arcpy.Parameter(
            displayName="Output Curve Number Raster",
            name="output_cn_raster",
            datatype="DERasterDataset",
            parameterType="Derived",
            direction="Output"
        )

        detailed_table_output = arcpy.Parameter(
            displayName="Output Detailed CN Table",
            name="output_detailed_cn_table",
            datatype="DETable",
            parameterType="Derived",
            direction="Output"
        )

        basin_summary_output = arcpy.Parameter(
            displayName="Output Basin CN Summary",
            name="output_basin_cn_summary",
            datatype="DETable",
            parameterType="Derived",
            direction="Output"
        )

        return [
            watershed,
            basin_field,
            lulc_raster,
            hsg_raster,
            cn_lookup,
            output_folder,
            dual_hsg,
            output_prefix,
            cn_raster_output,
            detailed_table_output,
            basin_summary_output
        ]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        spatial_checked_out = False

        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")
                spatial_checked_out = True
            else:
                raise arcpy.ExecuteError(
                    "The Spatial Analyst extension is required."
                )

            arcpy.env.overwriteOutput = True

            watershed = parameters[0].valueAsText
            basin_field = parameters[1].valueAsText
            lulc_raster = parameters[2].valueAsText
            hsg_raster = parameters[3].valueAsText
            cn_lookup = parameters[4].valueAsText
            output_folder = parameters[5].valueAsText
            dual_hsg = parameters[6].valueAsText
            prefix = parameters[7].valueAsText

            prefix = arcpy.ValidateTableName(prefix)

            watershed_desc = arcpy.Describe(watershed)
            lulc_desc = arcpy.Describe(lulc_raster)

            if watershed_desc.shapeType != "Polygon":
                raise arcpy.ExecuteError(
                    "Watershed input must be a polygon feature layer."
                )

            watershed_fields = [
                field.name for field in arcpy.ListFields(watershed)
            ]
            if basin_field not in watershed_fields:
                raise arcpy.ExecuteError(
                    "Basin field '{}' was not found.".format(basin_field)
                )

            lookup_fields = {
                field.name.upper(): field.name
                for field in arcpy.ListFields(cn_lookup)
            }
            required_lookup_fields = ["JOIN_ID", "CN", "LANDUSE"]
            missing_lookup_fields = [
                field
                for field in required_lookup_fields
                if field not in lookup_fields
            ]
            if missing_lookup_fields:
                raise arcpy.ExecuteError(
                    "The CN lookup table is missing required fields: "
                    + ", ".join(missing_lookup_fields)
                )

            join_lookup_field = lookup_fields["JOIN_ID"]
            cn_lookup_field = lookup_fields["CN"]
            landuse_lookup_field = lookup_fields["LANDUSE"]

            spatial_reference = lulc_desc.spatialReference
            if spatial_reference.type != "Projected":
                raise arcpy.ExecuteError(
                    "The LULC raster must use a projected coordinate system "
                    "for reliable area calculations."
                )

            meters_per_unit = spatial_reference.metersPerUnit
            if not meters_per_unit:
                raise arcpy.ExecuteError(
                    "Could not determine the linear units of the LULC raster."
                )

            acre_conversion_factor = (
                meters_per_unit ** 2
            ) / 4046.8564224

            gdb_name = prefix + "_Results.gdb"
            output_gdb = os.path.join(output_folder, gdb_name)

            if not arcpy.Exists(output_gdb):
                arcpy.management.CreateFileGDB(output_folder, gdb_name)

            hsg_reclass = os.path.join(
                output_gdb, prefix + "_HSG_Reclass"
            )
            combined_raster = os.path.join(
                output_gdb, prefix + "_LULC_HSG_Combined"
            )
            cn_raster = os.path.join(
                output_gdb, prefix + "_CN_Raster"
            )
            tabulate_table = os.path.join(
                output_gdb, prefix + "_Tabulate_Area"
            )
            long_table = os.path.join(
                output_gdb, prefix + "_Areas_Long"
            )
            detailed_table = os.path.join(
                output_gdb, prefix + "_Detailed_Report"
            )
            basin_summary = os.path.join(
                output_gdb, prefix + "_Basin_Summary"
            )

            arcpy.env.snapRaster = lulc_raster
            arcpy.env.cellSize = lulc_raster
            arcpy.env.extent = watershed
            arcpy.env.mask = watershed
            arcpy.env.outputCoordinateSystem = spatial_reference

            if dual_hsg.startswith("Drained"):
                hsg_mapping = [
                    [1, 1], [2, 2], [3, 3], [4, 4],
                    [5, 1], [6, 2], [7, 3]
                ]
            else:
                hsg_mapping = [
                    [1, 1], [2, 2], [3, 3], [4, 4],
                    [5, 4], [6, 4], [7, 4]
                ]

            arcpy.AddMessage("Reclassifying and aligning the HSG raster...")
            reclassified_hsg = arcpy.sa.Reclassify(
                hsg_raster,
                "Value",
                arcpy.sa.RemapValue(hsg_mapping),
                "NODATA"
            )
            reclassified_hsg.save(hsg_reclass)

            arcpy.AddMessage("Combining LULC and HSG rasters...")
            combined = arcpy.sa.Combine([lulc_raster, hsg_reclass])
            combined.save(combined_raster)

            excluded_fields = {"OBJECTID", "VALUE", "COUNT"}
            combination_fields = [
                field.name
                for field in arcpy.ListFields(combined_raster)
                if field.name.upper() not in excluded_fields
            ]
            if len(combination_fields) != 2:
                raise arcpy.ExecuteError(
                    "The toolbox could not identify the two input fields "
                    "in the combined raster."
                )

            lulc_field = combination_fields[0]
            hsg_field = combination_fields[1]

            arcpy.management.AddField(
                combined_raster, "JOIN_ID", "LONG"
            )
            arcpy.management.CalculateField(
                combined_raster,
                "JOIN_ID",
                "int(!{}!) * 10 + int(!{}!)".format(
                    lulc_field, hsg_field
                ),
                "PYTHON3"
            )

            arcpy.AddMessage("Joining the curve-number lookup table...")
            arcpy.management.JoinField(
                combined_raster,
                "JOIN_ID",
                cn_lookup,
                join_lookup_field,
                [cn_lookup_field, landuse_lookup_field]
            )

            missing_cn_count = 0
            with arcpy.da.SearchCursor(
                combined_raster, ["JOIN_ID", "CN"]
            ) as cursor:
                for join_id, cn_value in cursor:
                    if cn_value is None:
                        missing_cn_count += 1
                        arcpy.AddWarning(
                            "No CN lookup match for JOIN_ID " + str(join_id)
                        )

            if missing_cn_count > 0:
                raise arcpy.ExecuteError(
                    "{} LULC-HSG combinations have no matching CN. "
                    "Update the lookup table and rerun the tool.".format(
                        missing_cn_count
                    )
                )

            arcpy.AddMessage("Creating the curve-number raster...")
            cn_output = arcpy.sa.Lookup(combined_raster, "CN")
            cn_output.save(cn_raster)

            arcpy.AddMessage("Calculating combination areas by basin...")
            arcpy.sa.TabulateArea(
                watershed,
                basin_field,
                combined_raster,
                "Value",
                tabulate_table,
                arcpy.env.cellSize
            )

            value_fields = [
                field.name
                for field in arcpy.ListFields(tabulate_table)
                if field.name.upper().startswith("VALUE_")
            ]
            if not value_fields:
                raise arcpy.ExecuteError(
                    "Tabulate Area produced no combination fields. "
                    "Check watershed and raster overlap."
                )

            transpose_fields = [
                [field_name, field_name]
                for field_name in value_fields
            ]

            arcpy.AddMessage("Converting the area table to long format...")
            arcpy.management.TransposeFields(
                tabulate_table,
                transpose_fields,
                long_table,
                "COMBINATION",
                "AREA_SQ",
                [basin_field]
            )

            with arcpy.da.UpdateCursor(
                long_table, ["AREA_SQ"]
            ) as cursor:
                for row in cursor:
                    if row[0] is None or float(row[0]) == 0:
                        cursor.deleteRow()

            arcpy.management.AddField(
                long_table, "COMB_ID", "LONG"
            )
            arcpy.management.CalculateField(
                long_table,
                "COMB_ID",
                'int(!COMBINATION!.replace("VALUE_", ""))',
                "PYTHON3"
            )

            arcpy.management.JoinField(
                long_table,
                "COMB_ID",
                combined_raster,
                "Value",
                [lulc_field, hsg_field, "LANDUSE", "CN"]
            )

            arcpy.management.AddField(
                long_table, "HSG", "TEXT", field_length=10
            )
            hsg_code_block = (
                'def decode_hsg(value):\n'
                '    values = {1: "A", 2: "B", 3: "C", 4: "D"}\n'
                '    return values.get(int(value), "Unknown")\n'
            )
            arcpy.management.CalculateField(
                long_table,
                "HSG",
                "decode_hsg(!{}!)".format(hsg_field),
                "PYTHON3",
                hsg_code_block
            )

            arcpy.management.AddField(
                long_table, "AREA_AC", "DOUBLE"
            )
            arcpy.management.CalculateField(
                long_table,
                "AREA_AC",
                "float(!AREA_SQ!) * {}".format(
                    acre_conversion_factor
                ),
                "PYTHON3"
            )

            arcpy.management.AddField(
                long_table, "CN_AREA", "DOUBLE"
            )
            arcpy.management.CalculateField(
                long_table,
                "CN_AREA",
                "!CN! * !AREA_AC!",
                "PYTHON3"
            )

            arcpy.AddMessage("Creating the detailed reporting table...")
            arcpy.analysis.Statistics(
                long_table,
                detailed_table,
                [
                    ["AREA_AC", "SUM"],
                    ["CN_AREA", "SUM"]
                ],
                [
                    basin_field,
                    "HSG",
                    "LANDUSE",
                    "CN"
                ]
            )

            detailed_aliases = {
                "HSG": "Soil Group",
                "LANDUSE": "Cover Description",
                "CN": "Curve Number",
                "SUM_AREA_AC": "Area (acres)",
                "SUM_CN_AREA": "CN x Area"
            }
            detailed_fields = {
                field.name: field
                for field in arcpy.ListFields(detailed_table)
            }
            for field_name, alias in detailed_aliases.items():
                if field_name in detailed_fields:
                    arcpy.management.AlterField(
                        detailed_table,
                        field_name,
                        new_field_alias=alias
                    )

            arcpy.AddMessage("Creating the basin composite-CN summary...")
            arcpy.analysis.Statistics(
                long_table,
                basin_summary,
                [
                    ["AREA_AC", "SUM"],
                    ["CN_AREA", "SUM"]
                ],
                [basin_field]
            )

            arcpy.management.AddField(
                basin_summary, "COMPOSITE_CN", "DOUBLE"
            )
            arcpy.management.CalculateField(
                basin_summary,
                "COMPOSITE_CN",
                "!SUM_CN_AREA! / !SUM_AREA_AC! "
                "if !SUM_AREA_AC! else None",
                "PYTHON3"
            )

            arcpy.management.AlterField(
                basin_summary,
                "SUM_AREA_AC",
                new_field_alias="Total Area (acres)"
            )
            arcpy.management.AlterField(
                basin_summary,
                "SUM_CN_AREA",
                new_field_alias="Total CN x Area"
            )
            arcpy.management.AlterField(
                basin_summary,
                "COMPOSITE_CN",
                new_field_alias="Composite Curve Number"
            )

            parameters[8].value = cn_raster
            parameters[9].value = detailed_table
            parameters[10].value = basin_summary

            arcpy.AddMessage(
                "Curve-number workflow completed successfully."
            )
            arcpy.AddMessage("CN raster: " + cn_raster)
            arcpy.AddMessage("Detailed report: " + detailed_table)
            arcpy.AddMessage("Basin summary: " + basin_summary)

        except Exception:
            error_message = arcpy.GetMessages(2)
            if error_message:
                arcpy.AddError(error_message)
            raise

        finally:
            if spatial_checked_out:
                arcpy.CheckInExtension("Spatial")

    def postExecute(self, parameters):
        return
