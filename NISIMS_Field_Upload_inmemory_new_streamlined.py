#----------------------------------------------------------------------------------------------------------------------
# Name: NISIMS_field_upload.py
# Purpose: This script was created to automate the uploading of the NPS NISIMS field geodatabase. It was created to be
# used by the Data Manager for the EPMT program.
# Author: Jennifer Sieracki
# Created: 2014-06-03 14:55
# Updated: 2026-07-22 10:01
#----------------------------------------------------------------------------------------------------------------------

# Import modules
import arcpy, sys, traceback
from datetime import datetime
from multiprocessing import Process

# Input variables
Fldgdb = arcpy.GetParameterAsText(0)
TeamCd = arcpy.GetParameterAsText(1)
InPath = arcpy.GetParameterAsText(2)
LgcySt = arcpy.GetParameterAsText(3)
InGCS = arcpy.GetParameterAsText(4)
TZDT = arcpy.GetParameterAsText(5)
TZTM = arcpy.GetParameterAsText(6) 
DMgdb = arcpy.GetParameterAsText(7)
NISIMSgdb = arcpy.GetParameterAsText(8)

# Define variables
Newgdb = InPath + "\\" + str(TeamCd) + "_NISIMS_Field_" + str(time.strftime("%m%d%Y")) + "_toconvert.gdb"
Outgdb = InPath + "\\" + str(TeamCd) + "_NISIMS_" + str(time.strftime("%m%d%Y")) + "_toexport.gdb"
workcopy = InPath + "\\workcopy.gdb"
empty_cb = """def empty(fld):
    if fld == '':
        return None
    if fld == ' ':
        return None
    if fld == '<NULL>':
        return None
    if fld == '<Null>':
        return None
    else:
        return fld"""
guid_cb = """def CalcGUID():
    import uuid
    return '{' + str(uuid.uuid4()).upper() + '}'"""
count_cb = """rec=0
def autoIncrement():
    global rec
    pStart = 1
    pInterval = 1
    if(rec == 0):
        rec = pStart
    else:
        rec += pInterval
    return rec"""
trtac_cb = """def accalc(estac, cvrrt, totac):
    if cvrrt is None:
        return estac
    else:
        trtac = cvrrt*totac/100
        return trtac"""
act_cb = """def Calc(agtrt, appnm, actuse, estac, carvol, patnm, calcac):
    if actuse is None:
        if carvol is None:
            return
        elif appnm == "PERCENT SOLUTION":
            actuse = agtrt/100*carvol
            return actuse
        elif appnm == \"OUNCES PER GALLON\":
            actuse = agtrt*carvol
            return actuse
        elif appnm == \"GRAMS PER GALLON\":
            actuse = agtrt*carvol
            return actuse
        elif appnm == \"FLUID OUNCES PER GALLON\":
            actuse = agtrt*carvol
            return actuse
        elif appnm is None:
            return
        else:
            if patnm == "BROADCAST":
                actuse = agtrt * calcac
                return actuse
            else:            
                actuse = agtrt * estac
                return actuse
    else:
        return actuse"""
agt_cb = """def Calc(actnm, appnm, carnm):
    if actnm is None:
        if appnm == \"PERCENT SOLUTION\":
            return carnm
        elif appnm == \"OUNCES PER GALLON\":
            return \"OUNCES\"
        elif appnm == \"GRAMS PER GALLON\":
            return \"GRAMS\"
        elif appnm == \"FLUID OUNCES PER GALLON\":
            return \"FLUID OUNCES\"
        else:
            actnm = appnm[:-8]
            return actnm
    else:
        return actnm"""
rt_cb = """def Calc(agtrt, actuse, patnm, calcac, estac):
    if agtrt is None:
        if patnm == \"BROADCAST\":
            agtrt = actuse/calcac
            return agtrt
        else:
            agtrt = actuse/estac
            return agtrt
    else:
        return agtrt"""
rtuom_cb = """def Calc(appnm, actnm):
    if appnm is None:
        appnm = str(actnm + " PER ACRE")
        return appnm
    else:
        return appnm"""
adddt_cb = """def adddt(intm, indt):
    from datetime import datetime
    tmtx = str(intm)
    tmlen = len(tmtx)
    if tmlen < 12:
        dtdt = datetime.strptime(indt, '%m/%d/%Y %I:%M:%S %p')
        dt = dtdt.strftime('%m/%d/%Y')
        combined = f"{dt}{inttm}"
        dttm = datetime.strptime(dtadd, '%m/%d/%Y %I:%M:%S %p')
        return dttm
    else:
        return intm"""
fixtime = """def fixtm(badtm):
    from datetime import datetime
    dttx = str(badtm)
    dtlen = len(dttx)
    if dtlen > 12:
        tm = badtm.strftime('%I:%M:%S %p')
        return tm
    else:
        return badtm"""


def project_fc(fc):
    arcpy.AddMessage(fc)
    desc = arcpy.Describe(fc)
    arcpy.RepairGeometry_management(fc)
    fcct = arcpy.GetCount_management(fc).getOutput(0)
    if int(fcct) > 0:
        in_spatialref = desc.spatialreference
        if in_spatialref != srnad83:
            outnad83 = os.path.join(Newgdb, fc + "_nad83")
            extent = desc.extent
            outtrans = arcpy.ListTransformations(in_spatialref, srnad83, extent)
            transct = len(outtrans)
            if int(transct) > 0:
                arcpy.Project_management(fc, outnad83, srnad83, outtrans[0], in_spatialref)
            else:
                arcpy.Project_management(fc, outnad83, srnad83, "", in_spatialref)
        else:
            arcpy.CopyFeatures_management(fc, outnad83)

def append_to_new_gdb(fc, Newgdb):
    fc_list = ["PhotoLocation", "ProposedBiologicalTreatmentLn", "ProposedBiologicalTreatmentPt",
               "ProposedBiologicalTreatmentPy", "ProposedChemicalTreatmentLn", "ProposedChemicalTreatmentPt",
               "ProposedChemicalTreatmentPy", "ProposedOtherTreatmentLn", "ProposedOtherTreatmentPt",
               "ProposedOtherTreatmentPy", "BiologicalComponentLn", "BiologicalComponentPt", "BiologicalComponentPy",
               "FireComponentLn", "FireComponentPt", "FireComponentPy", "ManualComponentLn", "ManualComponentPt",
               "ManualComponentPy", "MechanicalComponentLn", "MechanicalComponentPt", "MechanicalComponentPy",
               "RestorationComponentLn", "RestorationComponentPt", "RestorationComponentPy", "RevegetationComponentLn",
               "RevegetationComponentPt", "RevegetationComponentPy", "WeedInfestationLn", "WeedInfestationPt",
               "WeedInfestationPy", "WeedSurveyLn", "WeedSurveyPt", "WeedSurveyPy"]
    chem_fc_list = ["ChemicalComponentLn", "ChemicalComponentPt", "ChemicalComponentPy"]
    for name in fc_list:
        if name in fc:
            arcpy.Append_management(fc, Newgdb + "\\" + name, "NO_TEST")
    for chem_name in chem_fc_list:
        if chem_name in fc:
            for field in arcpy.ListFields(fc, "CARR*"):
                if "CARRVOL_ME" in field.name:
                    arcpy.AddField_management(fc, "MIXVOL_ME", "DOUBLE")
                    arcpy.CalculateField_management(fc, "MIXVOL_ME", "!CARRVOL_ME!", "PYTHON3")
                    arcpy.DeleteField_management(fc, "CARRVOL_ME")
                elif "CARRUOM_NM" in field.name:
                    arcpy.AddField_management(fc, "MIXUOM_NM", "TEXT", "", "", 20)
                    arcpy.CalculateField_management(fc, "MIXUOM_NM", "!CARRUOM_NM!", "PYTHON3")
                    arcpy.DeleteField_management(fc, "CARRUOM_NM")
            arcpy.Append_management(fc, Newgdb + "\\TreatmentData\\" + chem_name, "NO_TEST")

def calculate_fields(fc):
    for field in arcpy.ListFields(fc):
        if field.type not in ["OID", "Geometry"]:
            if field.name not in ["SHAPE_Length", "SHAPE_Area", "Shape_Length", "Shape_Area"]:            
                if "NOTES" in field.name:
                    fldnm = str(field.name)
                    arcpy.CalculateField_management(fc, fldnm, "empty(!" + fldnm + "!)", "PYTHON3", empty_cb)
                elif "LOC_NM" in field.name:
                    fldnm = str(field.name)
                    arcpy.CalculateField_management(fc, fldnm, "empty(!" + fldnm + "!)", "PYTHON3", empty_cb)
                    arcpy.CalculateField_management(fc, fldnm, "!" + fldnm + "!.strip()", "PYTHON3")
                elif "TEXT" in field.type:
                    fldnm = str(field.name)
                    arcpy.CalculateField_management(fc, fldnm, "!" + fldnm + "!.upper()", "PYTHON3")
                    arcpy.CalculateField_management(fc, fldnm, "empty(!" + fldnm + "!)", "PYTHON3", empty_cb)
                    arcpy.CalculateField_management(fc, fldnm, "!" + fldnm + "!.strip()", "PYTHON3")
                else:
                    fldnm = str(field.name)
                    arcpy.CalculateField_management(fc, fldnm, "empty(!" + fldnm + "!)", "PYTHON3", empty_cb)  

def project_albers_fc(dataset):
    arcpy.CreateFeatureDataset_management(workcopy, dataset, sralbers)
    fcs = arcpy.ListFeatureClasses()
    if fcs is not None and len(fcs) > 0:
        for fc in fcs:
            fcct = arcpy.management.GetCount(fc).getOutput(0)
            if int(fcct) > 0:
                arcpy.RepairGeometry_management(fc)
                desc = arcpy.Describe(fc)
                arcpy.AddMessage(desc.name + " being processed.")
                fld_spatialref = desc.spatialReference
                if fld_spatialref != sralbers:
                    outgcs = os.path.join(workcopy + "\\" + dataset + "\\" + fc + "_gcs")
                    extent = desc.extent
                    outtrans = arcpy.ListTransformations(fld_spatialref, sralbers, extent)
                    transct = len(outtrans)
                    if int(transct) > 0:
                        arcpy.Project_management(fc, outgcs, sralbers, outtrans[0], fld_spatialref)
                    else:
                        arcpy.Project_management(fc, outgcs, sralbers, "", fld_spatialref)
                else:
                    arcpy.CopyFeatures_management(fc, outgcs)
                arcpy.CopyFeatures_management(outgcs, "memory\\" + fc + "_gcs")

def buffer_lines_and_points(fccat):
    fcs = arcpy.ListFeatureClasses(fccat + "*_gcs")
    if fcs is not None and len(fcs) > 0:
        for fc in fcs:
            desc = arcpy.Describe(fc)
            arcpy.AddMessage(desc.name + " being processed.")
            fcct = arcpy.GetCount_management(fc).getOutput(0)
            if int(fcct) > 0:
                # If point data, buffer
                if "Pt_gcs" in fc:
                    ptall = arcpy.GetCount_management(fc).getOutput(0)
                    if int(ptall) > 0:
                        arcpy.Buffer_analysis(fc, fc + "Py_gcs", "BUFFER_M", "FULL", "ROUND", "NONE")

                # If Line data, buffer
                if "Ln_gcs" in fc:
                    lnall = arcpy.GetCount_management(fc).getOutput(0)
                    if int(lnall) > 0:
                        arcpy.Select_analysis(fc, fc + "LN_left", "\"BUFDIR\" = \'LEFT\'")
                        lnl = arcpy.GetCount_management(fc + "LN_left").getOutput(0)
                        if int(lnl) > 0:
                            arcpy.Buffer_analysis(fc + "LN_left", fc + "LNtoPY_left", "BUFFER_M", "LEFT", "ROUND", "NONE")
                        arcpy.Select_analysis(fc, fc + "LN_right", "\"BUFDIR\" = \'RIGHT\'")
                        lnr = arcpy.GetCount_management(fc + "LN_right").getOutput(0)
                        if int(lnr) > 0:
                            arcpy.Buffer_analysis(fc + "LN_right", fc + "LNtoPY_right", "BUFFER_M", "RIGHT", "ROUND", "NONE")
                        arcpy.Select_analysis(fc, fc + "LN_full", "\"BUFDIR\" = \'FULL\'")
                        lnf = arcpy.GetCount_management(fc + "LN_full").getOutput(0)
                        if int(lnf) > 0:
                            arcpy.Buffer_analysis(fc + "LN_full", fc + "LNtoPY_full", "BUFFER_M", "FULL", "ROUND", "NONE")
                if fccat == "WeedSurvey" or fccat == "WeedInfestation":
                    arcpy.CreateFeatureclass_management("memory", fccat + "LnPy_gcs", "POLYGON", workcopy + "\\" + fccat + "Data\\" + fccat + "Py", "", "", sralbers)
                elif fccat == "ProposedBiological" or fccat == "ProposedChemical" or fccat == "ProposedOther":
                    arcpy.CreateFeatureclass_management("memory", fccat + "LnPy_gcs", "POLYGON", workcopy + "\\ProposedTreatmentData\\" + fccat + "TreatmentPy", "", "", sralbers)
                else:
                    arcpy.CreateFeatureclass_management("memory", fccat + "LnPy_gcs", "POLYGON", workcopy + "\\TreatmentData\\" + fccat + "ComponentPy", "", "", sralbers)
                LNfc = arcpy.ListFeatureClasses(fccat + "*LNtoPY*")
                LNct = len(LNfc)
                if LNct > 0:
                    arcpy.Append_management(LNfc, fccat + "LnPy_gcs", "NO_TEST")              

def add_and_calculate(fc, field_list, type_list, length_list, query_list, sub_query_list):
    for i in range(len(field_list)):
        arcpy.AddField_management(fc, field_list[i], type_list[i], '', '', length_list[i])
        if sub_query_list[i] != '':
            arcpy.CalculateField_management(fc, field_list[i], query_list[i], "PYTHON3", sub_query_list[i])
        else:
            arcpy.CalculateField_management(fc, field_list[i], query_list[i], "PYTHON3")
            
def state_and_county(fccat):
    arcpy.AddField_management(workcopy + "\\" + fccat + "_allpy", "Rejoin_ID", "LONG")
    arcpy.CalculateField_management(workcopy + "\\" + fccat + "_allpy", "Rejoin_ID", "autoIncrement()", "PYTHON3", count_cb)
    arcpy.MakeXYEventLayer_management(workcopy + "\\" + fccat + "_allpy", "newx", "newy", fccat + "_lyr", sralbers)
    arcpy.management.CreateFeatureclass(workcopy, fccat + "_cntrpt", "Point", fccat + "_lyr", "DISABLED", "DISABLED", sralbers)
    arcpy.Append_management(fccat + "_lyr", workcopy + "\\" + fccat + "_cntrpt")
    if fccat == "WeedSurveyData" or fccat == "WeedInfestationData":
        arcpy.CreateFeatureDataset_management(workcopy, fccat + "UTM", new_spatialref)
        arcpy.Project_management(workcopy + "\\" + fccat + "_cntrpt", workcopy + "\\" + fccat + "UTM\\" + fccat + "_cntrpt_utm", new_spatialref)
        arcpy.CopyFeatures_management(workcopy + "\\" + fccat + "UTM\\" + fccat + "_cntrpt_utm", fccat + "_cntrpt_utm")
    else:
        arcpy.Project_management(workcopy + "\\" + fccat + "_cntrpt", workcopy + "\\TreatmentDataUTM\\" + fccat + "_cntrpt_utm", new_spatialref)
        arcpy.CopyFeatures_management(workcopy + "\\TreatmentDataUTM\\" + fccat + "_cntrpt_utm", fccat + "_cntrpt_utm")
    arcpy.AddField_management(fccat + "_cntrpt_utm", "STUSPS_1", "TEXT", "", "", 20)
    arcpy.AddField_management(fccat + "_cntrpt_utm", "GEOID_1", "TEXT", "", "", 5)
    stcty = arcpy.FieldMappings()
    stcty.addTable(fccat + "_cntrpt_utm")
    stcty.addTable(Outgdb + "\\Reference\State")
    arcpy.SpatialJoin_analysis(fccat + "_cntrpt_utm", Outgdb + "\\Reference\\State", fccat + "_st", "JOIN_ONE_TO_ONE", "KEEP_ALL", stcty, "INTERSECT", "", "")
    arcpy.CalculateField_management(fccat + "_st", "STUSPS_1", "!STUSPS!", "PYTHON3")
    arcpy.DeleteField_management(fccat + "_st", "GEOID")
    stcty.addTable(Outgdb + "\\Reference\County")
    arcpy.SpatialJoin_analysis(fccat + "_st", Outgdb + "\\Reference\\County", fccat + "_stcty", "JOIN_ONE_TO_ONE", "KEEP_ALL", stcty, "INTERSECT", "", "")
    arcpy.CalculateField_management(fccat + "_stcty", "GEOID_1", "!GEOID!", "PYTHON3")
    if fccat == "WeedSurveyData" or fccat == "WeedInfestationData":
        arcpy.Project_management(workcopy + "\\" + fccat + "_allpy", workcopy + "\\" + fccat + "UTM\\" + fccat + "_allpyutm", new_spatialref)
        arcpy.CopyFeatures_management(workcopy + "\\" + fccat + "UTM\\" + fccat + "_allpyutm", fccat + "_allpyutm")
    else:
        arcpy.Project_management(workcopy + "\\" + fccat + "_allpy", workcopy + "\\TreatmentDataUTM\\" + fccat + "_allpyutm", new_spatialref)
        arcpy.CopyFeatures_management(workcopy + "\\TreatmentDataUTM\\" + fccat + "_allpyutm", fccat + "_allpyutm")
    arcpy.management.JoinField(fccat + "_allpyutm", "Rejoin_ID", fccat + "_stcty", "Rejoin_ID", ("STUSPS_1", "GEOID_1", "TIMEZONE", "DST"))
    arcpy.CopyFeatures_management(fccat + "_allpyutm", fccat + "_join")

def convert_utc_dates(fccat, begindt, enddt):
    if 'true' in TZDT:
        arcpy.CopyFeatures_management(fccat + "_join", fccat + "_tz")
        arcpy.CopyRows_management(DMgdb + "\\DST", "DST")
        arcpy.DeleteIdentical_management(fccat + "_tz", "TIMEZONE")
        with arcpy.da.SearchCursor(fccat + "_tz", ["TIMEZONE", "DST"]) as cursor:
            for row in cursor:
                tzval = str(row[0])
                arcpy.Select_analysis(fccat + "_join", fccat + "_tz_" + str(tzval) + "_NoDST", "\"TIMEZONE\" = \'" + str(tzval) + "\' AND \"DST\" = \'FALSE\'")
                recct = arcpy.GetCount_management(fccat + "_tz_" + str(tzval) + "_NoDST").getOutput(0)
                if int(recct) > 0:
                    arcpy.ConvertTimeZone_management(fccat + "_tz_" + str(tzval)+ "_NoDST", begindt, "UTC", "BEGIN_DT_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")
                    arcpy.CalculateField_management(fccat + "_tz_" + str(tzval)+ "_NoDST", begindt, "!BEGIN_DT_temp!", "PYTHON3")
                    if enddt != 0:
                        arcpy.ConvertTimeZone_management(fccat + "_tz_" + str(tzval)+ "_NoDST", enddt, "UTC", "END_DT_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")                    
                        arcpy.CalculateField_management(fccat + "_tz_" + str(tzval)+ "_NoDST", enddt, "!END_DT_temp!", "PYTHON3")
                        arcpy.CopyFeatures_management(fccat + "_tz_" + str(tzval) + "_NoDST", fccat + "_tz_merge_" + str(tzval) + "_NoDST")
                    if enddt == 0:
                        arcpy.CopyFeatures_management(fccat + "_tz_" + str(tzval) + "_NoDST", fccat + "_tz_merge_" + str(tzval) + "_NoDST")
                arcpy.Select_analysis(fccat + "_join", workcopy + "\\" + fccat + "_tz_" + str(tzval) + "_DST", "\"TIMEZONE\" = \'" + str(tzval) + "\' AND \"DST\" = \'TRUE\'")
                recct = arcpy.GetCount_management(workcopy + "\\" + fccat + "_tz_" + str(tzval) + "_DST").getOutput(0)
                if int(recct) > 0:
                    arcpy.AddField_management(workcopy + "\\" + fccat + "_tz_" + str(tzval) + "_DST", "DST_FL", "TEXT", "", "", 5)
                    dst_ranges = []
                    with arcpy.da.SearchCursor("DST", ["START_DT", "END_DT"]) as cursor1:
                        for row1 in cursor1:
                            dst_ranges.append((row1[0], row1[1]))
                    with arcpy.da.UpdateCursor(workcopy + "\\" + fccat + "_tz_" + str(tzval) + "_DST", [begindt, "DST_FL"]) as cursor2:
                        for row2 in cursor2:
                            begdt = row2[0]
                            if isinstance(begdt, datetime):
                                if row2[1] == 'FALSE' or row2[1] is None:
                                    is_dst = any(start <= begdt <= end for start, end in dst_ranges)
                                    new_val = 'TRUE' if is_dst else 'FALSE'
                                    if row2[1] != new_val:
                                        row2[1] = new_val
                                        cursor2.updateRow(row2)
                    arcpy.Select_analysis(workcopy + "\\" + fccat + "_tz_" + str(tzval) + "_DST", fccat + "_tz_" + str(tzval) + "_NoDST2", "\"DST_FL\" = \'FALSE\'")
                    recct = arcpy.GetCount_management(fccat + "_tz_" + str(tzval) + "_NoDST2").getOutput(0)
                    if int(recct) > 0:
                        arcpy.ConvertTimeZone_management(fccat + "_tz_" + str(tzval) + "_NoDST2", begindt, "UTC", "BEGIN_DT_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")
                        arcpy.CalculateField_management(fccat + "_tz_" + str(tzval) + "_NoDST2", begindt, "!BEGIN_DT_temp!", "PYTHON3")
                        arcpy.CopyFeatures_management(fccat + "_tz_" + str(tzval) + "_NoDST2", fccat + "_tz_start_" + str(tzval) + "_NoDST2")
                        if enddt == 0:
                            arcpy.CopyFeatures_management(fccat + "_tz_start_" + str(tzval) + "_NoDST2", fccat + "_tz_merge_" + str(tzval) + "_NoDST2")
                    arcpy.Select_analysis(workcopy + "\\" + fccat + "_tz_" + str(tzval) + "_DST", fccat + "_tz_" + str(tzval) + "_YesDST", "\"DST_FL\" = \'TRUE\'")
                    recct = arcpy.GetCount_management(fccat + "_tz_" + str(tzval) + "_YesDST").getOutput(0)
                    if int(recct) > 0:
                        arcpy.ConvertTimeZone_management(fccat + "_tz_" + str(tzval) + "_YesDST", begindt, "UTC", "BEGIN_DT_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_ADJUSTED_FOR_DST")
                        arcpy.CalculateField_management(fccat + "_tz_" + str(tzval) + "_YesDST", begindt, "!BEGIN_DT_temp!", "PYTHON3")
                        arcpy.CopyFeatures_management(fccat + "_tz_" + str(tzval) + "_YesDST", fccat + "_tz_start_" + str(tzval) + "_YesDST") 
                        if enddt == 0:
                            arcpy.CopyFeatures_management(fccat + "_tz_start_" + str(tzval) + "_YesDST", fccat + "_tz_merge_" + str(tzval) + "_YesDST")
                    if enddt != 0:
                        tzlist = arcpy.ListFeatureClasses(fccat + "_tz_start_" + str(tzval) + "*")
                        tzfm = arcpy.FieldMappings()
                        tzfm = tzfm.addTable(fccat + "_join")
                        arcpy.Merge_management(tzlist, workcopy + "\\" + fccat + "_start", tzfm)
                        dst_ranges = []
                        with arcpy.da.SearchCursor("DST", ["START_DT", "END_DT"]) as cursor1:
                            for row1 in cursor1:
                                dst_ranges.append((row1[0], row1[1]))
                            with arcpy.da.UpdateCursor(workcopy + "\\" + fccat + "_start", [enddt, "DST_FL"]) as cursor2:
                                for row2 in cursor2:
                                    edt = row2[0]
                                    if isinstance(edt, datetime):
                                        if row2[1] == 'FALSE' or row2[1] is None:
                                            is_dst = any(start <= edt <= end for start, end in dst_ranges)
                                            new_val = 'TRUE' if is_dst else 'FALSE'
                                            if row2[1] != new_val:
                                                row2[1] = new_val
                                                cursor2.updateRow(row2)
                        arcpy.Select_analysis(workcopy + "\\" + fccat + "_start", fccat + "_tz_" + str(tzval) + "_NoDST2", "\"DST_FL\" = \'FALSE\'")
                        recct = arcpy.GetCount_management(fccat + "_tz_" + str(tzval) + "_NoDST2").getOutput(0)
                        if int(recct) > 0:
                            arcpy.ConvertTimeZone_management(fccat + "_tz_" + str(tzval) + "_NoDST2", enddt, "UTC", "END_DT_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")                     
                            arcpy.CalculateField_management(fccat + "_tz_" + str(tzval) + "_NoDST2", enddt, "!END_DT_temp!", "PYTHON3")
                            arcpy.CopyFeatures_management(fccat + "_tz_" + str(tzval) + "_NoDST2", fccat + "_tz_merge_" + str(tzval) + "_NoDST2")
                        arcpy.Select_analysis(workcopy + "\\" + fccat + "_start", fccat + "_tz_" + str(tzval) + "_YesDST", "\"DST_FL\" = \'TRUE\'")
                        recct = arcpy.GetCount_management(fccat + "_tz_" + str(tzval) + "_YesDST").getOutput(0)
                        if int(recct) > 0:
                            arcpy.ConvertTimeZone_management(fccat + "_tz_" + str(tzval) + "_YesDST", enddt, "UTC", "END_DT_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_ADJUSTED_FOR_DST")  
                            arcpy.CalculateField_management(fccat + "_tz_" + str(tzval) + "_YesDST", enddt, "!END_DT_temp!", "PYTHON3")
                            arcpy.CopyFeatures_management(fccat + "_tz_" + str(tzval) + "_YesDST", fccat + "_tz_merge_" + str(tzval) + "_YesDST")            
        tzlist = arcpy.ListFeatureClasses(fccat + "_tz_merge_*")
        tzfm = arcpy.FieldMappings()
        tzfm = tzfm.addTable(fccat + "_join")
        arcpy.Merge_management(tzlist, fccat + "_join2", tzfm)
    else:
        arcpy.CopyFeatures_management(fccat + "_join", fccat + "_join2")

def update_chem_time(fclist):
    for fc in fclist:
        arcpy.AddField_management(fc, "Begtm", "TEXT", "", "", 11)
        arcpy.AddField_management(fc, "Endtm", "TEXT", "", "", 11)
        arcpy.CalculateField_management(fc, "Begtm", "fixtm(!TRT_BEG_TM!)", "PYTHON3", fixtime)
        arcpy.CalculateField_management(fc, "Endtm", "fixtm(!TRT_END_TM!)", "PYTHON3", fixtime)
        arcpy.DeleteField_management(fc, ["TRT_BEG_TM", "TRT_END_TM"])
        arcpy.AddField_management(fc, "TRT_BEG_TM", "TEXT", "", "", 11)
        arcpy.AddField_management(fc, "TRT_END_TM", "TEXT", "", "", 11)
        arcpy.CalculateField_management(fc, "TRT_BEG_TM", "!Begtm!", "PYTHON3")
        arcpy.CalculateField_management(fc, "TRT_END_TM", "!Endtm!", "PYTHON3")

def species_append(fccat, guidfield, outtable):
    SppNum = 1
    for field in arcpy.ListFields(fccat + "_spp", "SCNTFC_CD*"):
        arcpy.Select_analysis(fccat + "_spp", "spptb2_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
        RecNum = arcpy.GetCount_management("spptb2_" + str(SppNum)).getOutput(0)
        if int(RecNum) > 0:
            arcpy.CopyFeatures_management("spptb2_" + str(SppNum), "spptb_" + str(SppNum))
            arcpy.CalculateField_management("spptb_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON3")
            SppNum += 1
    sppfld = arcpy.ListFeatureClasses("spptb_*")
    SppCt = len(sppfld)
    if SppCt > 0:
        arcpy.Append_management(sppfld, fccat + "_spp")
        arcpy.Select_analysis(fccat + "_spp", fccat + "_spptbsel", "\"SCNTFC_CD\" IS NOT NULL")
        sppcnt = arcpy.GetCount_management(fccat + "_spptbsel").getOutput(0)
        if int(sppcnt) > 0:
            row_pairs = set()
            with arcpy.da.UpdateCursor(fccat + "_spptbsel", [guidfield, "SCNTFC_CD"]) as cursor:
                for row in cursor:
                    row_pair = tuple(row)
                    if row_pair in row_pairs:
                        cursor.deleteRow()
                    else:
                        row_pairs.add(row_pair)
            arcpy.CopyRows_management(fccat + "_spptbsel", fccat + "spptb_all")
            wsspfm = arcpy.FieldMappings()
            wsspfm.addTable(Outgdb + "\\" + outtable)
            arcpy.Append_management(fccat + "spptb_all", Outgdb + "\\" + outtable, "NO_TEST", wsspfm)

def coop_pers_append(fccat):
    arcpy.CopyFeatures_management(fcccat + "_fc", fccat + "_coop")
    CoopNum = 1
    for field in arcpy.ListFields(fccat + "_coop", "COOP_PERS*"):
        arcpy.Select_analysis(fccat + "_coop", "coop_" + str(CoopNum), "\"" + field.name + "\"" + " IS NOT NULL")
        RecNum = arcpy.GetCount_management("coop_" + str(CoopNum)).getOutput(0)
        if int(RecNum) > 0:
            arcpy.CalculateField_management("coop_" + str(CoopNum), "COOP_PERS", "!" + field.name + "!", "PYTHON3")
            CoopNum += 1
    coopfld = arcpy.ListFeatureClasses("coop_*")
    arcpy.Append_management(coopfld, fccat + "_coop")
    arcpy.Select_analysis(fccat + "_coop", fccat + "_coopsel", "\"COOP_PERS\" IS NOT NULL")
    coopcnt = arcpy.GetCount_management(fccat + "_coopsel").getOutput(0)
    if int(coopcnt) > 0:
        row_pairs = set()
        with arcpy.da.UpdateCursor(fccat + "_coopsel", ["COOP_PERS", "PROP_TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management(fccat + "_coopsel", fccat + "coop_all")
        ptcpfm = arcpy.FieldMappings()
        ptcpfm.addTable(Outgdb + "\\PROPOSALCOOPERATOR")
        arcpy.Append_management(fccat + "coop_all", Outgdb + "\\PROPOSALCOOPERATOR", "NO_TEST", ptcpfm)

def nepa_append(fccat):
    arcpy.CopyFeatures_management(fccat + "_fc", fccat + "_nepa")
    NEPANum = 1
    for field in arcpy.ListFields(fccat + "_nepa", "NEPA_NR*"):
        arcpy.Select_analysis(fccat + "_nepa", "nepa" + str(NEPANum), "\"" + field.name + "\"" + " IS NOT NULL")
        RecNum = arcpy.GetCount_management("nepa" + str(NEPANum)).getOutput(0)
        if int(RecNum) > 0:
            arcpy.CalculateField_management("nepa" + str(NEPANum), "NEPA_NR", "!" + field.name + "!", "PYTHON3")
            NEPANum += 1
    nepafld = arcpy.ListFeatureClasses("nepa_*")
    arcpy.Append_management(nepafld, fccat + "_nepa")
    arcpy.Select_analysis(fccat + "_nepa", fccat + "_nepasel", "\"NEPA_NR\" IS NOT NULL")
    nepacnt = arcpy.GetCount_management(fccat + "_nepasel").getOutput(0)
    if int(nepacnt) > 0:
        row_pairs = set()
        with arcpy.da.UpdateCursor(fccat + "_nepasel", ["NEPA_NR", "PROP_TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management(fccat + "_nepasel", fccat + "nepa_all")
        ptnepafm = arcpy.FieldMappings()
        ptnepafm.addTable(Outgdb + "\\TREATMENTPROPOSALNUMBERS")
        arcpy.Append_management(fccat + "nepa_all", Outgdb + "\\TREATMENTPROPOSALNUMBERS", "NO_TEST", pbtnepafm)

def project_albers_treat(treatcat):
    fcs = arcpy.ListFeatureClasses(treatcat + "*")
    if fcs is not None and len(fcs) > 0:
        for fc in fcs:
            arcpy.RepairGeometry_management(fc)
            desc = arcpy.Describe(fc)
            arcpy.AddMessage(desc.name + " is being processed.")
            fcct = arcpy.GetCount_management(fc).getOutput(0)
            if int(fcct) > 0:
                fld_spatialref = desc.spatialReference
                if fld_spatialref != sralbers:
                    outgcs = os.path.join(workcopy + "\\TreatmentDataAlbers\\" + fc + "_gcs")
                    extent = desc.extent
                    outtrans = arcpy.ListTransformations(fld_spatialref, sralbers, extent)
                    transct = len(outtrans)
                    if int(transct) > 0:
                        arcpy.Project_management(fc, outgcs, sralbers, outtrans[0], fld_spatialref)
                    else:
                        arcpy.Project_management(fc, outgcs, sralbers, "", fld_spatialref)
                else:
                    arcpy.CopyFeatures_management(fc, outgcs)
                arcpy.CopyFeatures_management(outgcs, "memory\\" + fc + "_gcs")

def calculate_treat_acres(treatcat):
    arcpy.AddField_management(treatcat + "_join2", "PARKACRE_ME", "DOUBLE")
    arcpy.AddField_management(treatcat + "_join2", "joinid", "LONG")
    arcpy.CalculateField_management(treatcat + "_join2", "joinid", "autoIncrement()", "PYTHON3", count_cb)
    arcpy.Intersect_analysis([treatcat + "_join2", Outgdb + "\\Reference\\NPSbound"], treatcat + "_park")
    arcpy.Dissolve_management(treatcat + "_park", workcopy + "\\" + treatcat + "_dis", ["joinid"])
    arcpy.Project_management( workcopy + "\\" + treatcat + "_dis", workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_albers", sralbers)
    arcpy.CopyFeatures_management(workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_albers", treatcat + "_albers")
    arcpy.AddField_management(treatcat + "_albers", "parkacre", "DOUBLE")
    arcpy.CalculateField_management(treatcat + "_albers", "parkacre", "!SHAPE.AREA@ACRES!", "PYTHON3")
    arcpy.CopyFeatures_management(treatcat + "_join2", workcopy + "\\" + treatcat + "_join2")
    arcpy.Project_management(workcopy + "\\" + treatcat + "_join2", workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_alb2", sralbers)
    arcpy.JoinField_management(workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_alb2", "joinid", treatcat + "_albers", "joinid")
    arcpy.CalculateField_management(workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_alb2", "PARKACRE_ME", "!parkacre!", "PYTHON3")
    arcpy.AddField_management(workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_alb2", "CLCACRE_ME", "DOUBLE")
    arcpy.CalculateField_management(workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_alb2", "CLCACRE_ME", "!SHAPE.AREA@ACRES!", "PYTHON3")
    arcpy.AddField_management(workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_alb2", "CVR_UOM_NM", "TEXT", "", "", 20)
    arcpy.CalculateField_management(workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_alb2", "CVR_UOM_NM", "\"ACRES\"")
    arcpy.Project_management(workcopy + "\\TreatmentDataAlbers\\" + treatcat + "_alb2", workcopy + "\\TreatmentDataUTM\\" + treatcat + "_utm2", new_spatialref)
    arcpy.CopyFeatures_management(workcopy + "\\TreatmentDataUTM\\" + treatcat + "_utm2", treatcat + "_utm2")

def treat_species_append(fccat):
    SppNum = 1
    for field in arcpy.ListFields(fccat + "_spp", "SCNTFC_CD*"):
        arcpy.Select_analysis(fccat + "_spp", fccat + "tb3_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
        RecNum = arcpy.GetCount_management(fccat + "tb3_" + str(SppNum)).getOutput(0)
        if int(RecNum) > 0:
            arcpy.CalculateField_management(fccat + "tb3_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON3")
            SpNR = str(field.name)
            SpNR = SpNR.strip("SCNTFC_CD")
            SpCov = str("EST_CVR_RT" + SpNR)
            arcpy.CalculateField_management(fccat + "tb3_" + str(SppNum), "EST_CVR_RT", "!" + SpCov + "!", "PYTHON3")
            SpQty = str("TRT_QTY" + SpNR)
            arcpy.CalculateField_management(fccat + "tb3_" + str(SppNum), "TRT_QTY", "!" + SpQty + "!", "PYTHON3")                
            SppNum += 1
    sppfld = arcpy.ListFeatureClasses(fccat + "tb3_*")
    arcpy.Append_management(sppfld, fccat + "_spp")
    arcpy.Select_analysis(fccat + "_spp", fccat + "_sppsel", "\"SCNTFC_CD\" IS NOT NULL")
    arcpy.CalculateField_management(fccat + "_sppsel", "cvrrttx", "!EST_CVR_RT!", "PYTHON3")
    arcpy.AddField_management(fccat + "_sppsel", "trtqtytx", "TEXT", "", "", 20)
    arcpy.CalculateField_management(fccat + "_sppsel", "trtqtytx", "!TRT_QTY!", "PYTHON3")
    sppcnt = arcpy.GetCount_management(fccat + "_sppsel").getOutput(0)
    if int(sppcnt) > 0:
        row_pairs = set()
        with arcpy.da.UpdateCursor(fccat + "_sppsel", ["SCNTFC_CD", "cvrrttx", "trtqtytx", "TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management(fccat + "_sppsel", fccat + "_sppall")
        arcpy.Statistics_analysis(fccat + "_sppall", fccat + "_cvrsum", [["EST_CVR_RT", "SUM"]], ["TRT_GUID","CLCACRE_ME"])
        sppfm = arcpy.FieldMappings()
        sppfm.addTable(Outgdb + "\\TREATMENTSPECIES")
        arcpy.Append_management(fccat + "_sppall", Outgdb + "\\TREATMENTSPECIES", "NO_TEST", sppfm)

def remove_nonzeroes(fctype, field, relfield):
    fcs = arcpy.ListFeatureClasses(fctype + "*")
    for fc in fcs:
        with arcpy.da.UpdateCursor(fc, [field, relfield]) as cursor:
            for row in cursor:
                if row[0] == 0 and row[1] is None:
                    row[0] is None

                
try:

    # Copy data management gdb
    srnad83 = arcpy.Describe(DMgdb + "\\PhotoLocation").spatialReference
    arcpy.env.workspace = Fldgdb
    arcpy.Copy_management(DMgdb, Newgdb)
    arcpy.AddMessage("Adding data to gdb.")

    # Project Data to NAD83
    for fc in arcpy.ListFeatureClasses():
        project_fc(fc)
    for ds in arcpy.ListDatasets():
        gdb = (Fldgdb)
        feature_dataset = ds
        arcpy.env.workspace = os.path.join(gdb, feature_dataset)
        for fc in arcpy.ListFeatureClasses():
            project_fc(fc)    

    # Copy feature classes into unlocked copy of field geodatabase
    arcpy.env.workspace = Newgdb
    fcs = arcpy.ListFeatureClasses("*_nad83")
    if fcs is not None and len(fcs) > 0:
        for fc in fcs:
            append_to_new_gdb(fc, Newgdb)
            arcpy.Delete_management(fc)
    for ds in arcpy.ListDatasets():
        arcpy.env.workspace = ds
        fcs = arcpy.ListFeatureClasses("*_nad83")
        if fcs is not None and len(fcs) > 0:
            for fc in fcs:
                append_to_new_gdb(fc, Newgdb)
                arcpy.Delete_management(fc)
                
    # Fix empty field values
    arcpy.env.workspace = Newgdb
    fcs = arcpy.ListFeatureClasses()
    if fcs is not None and len(fcs) > 0:
        for fc in fcs:
            calculate_fields(fc)
    for ds in arcpy.ListDatasets():
        arcpy.env.workspace = ds
        fcs = arcpy.ListFeatureClasses()
        if fcs is not None and len(fcs) > 0:
            for fc in fcs:
                calculate_fields(fc)
    arcpy.env.workspace = Newgdb

    # Create a copy of the field geodatabase
    arcpy.Copy_management(Newgdb, workcopy)
    arcpy.Copy_management(NISIMSgdb, Outgdb)

    # Define coordinate system variables
    new_spatialref = arcpy.Describe(Outgdb + "\\WeedSurveyLocation").spatialReference
    sralbers = arcpy.SpatialReference(int(InGCS))    
    
    # Set WeedSurveyData as workspace
    arcpy.env.workspace = workcopy + "\\WeedSurveyData"

    # Check for data in each feature class and project if needed
    arcpy.AddMessage("Processing weed survey data.")
    project_albers_fc("WeedSurveyDataAlbers")

    # Buffer point and line data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("WeedSurvey")            

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "WeedSurveyData_allpy", "POLYGON", workcopy + "\\WeedSurveyData\\WeedSurveyPy", "DISABLED", "DISABLED", sralbers)
    WSPy = arcpy.ListFeatureClasses("WeedSurvey*Py_gcs")
    WSPyCt = len(WSPy)
    survpy = arcpy.FieldMappings()
    survpy.addTable(workcopy + "\\WeedSurveyData\\WeedSurveyPy")
    if WSPyCt > 0:
        arcpy.Append_management(WSPy, workcopy + "\\WeedSurveyData_allpy", "NO_TEST", survpy)

        # Calculate acreage
        add_and_calculate(workcopy + "\\WeedSurveyData_allpy", ["SRVY_ME", "newx", "newy", "CNTR_PT_CN"], 
                          ["DOUBLE", "DOUBLE", "DOUBLE", "TEXT"], [0, 0, 0, 50], 
                          ["!SHAPE.AREA@ACRES!", "!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], 
                          ['', '', '', ''])

        # Calculate State and County fields
        state_and_county("WeedSurveyData")
        add_and_calculate("WeedSurveyData_join", ["STATE_CD", "COUNTY_CD"], ["TEXT", "TEXT"], [2, 5], ["!STUSPS_1!", "!GEOID_1!"], ['', ''])        

        # Convert UTC dates
        convert_utc_dates("WeedSurveyData", "BEGIN_DT", "END_DT")
                
        # Append to WeedSurveyLocation
        arcpy.CopyFeatures_management("WeedSurveyData_join2", "WeedSurveyData_fc")
        add_and_calculate("WeedSurveyData_fc", ["txBDate_fc", "txEDate_fc", "perim", "newxtx", "newytx", "srvytx_fc", "newid", "SURV_GUID", "RECORDER_fc", "WSA_TY_NM_fc", "LOC_NM_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "SHORT", "GUID", "TEXT", "TEXT", "TEXT"], [30, 30, 20, 20, 20, 20, 0, 0, 50, 10, 100], 
                          ["!BEGIN_DT!", "!END_DT!", "str(!SHAPE.LENGTH@METERS!)", "!newx!", "!newy!", "!SRVY_ME!", "autoIncrement()", "CalcGUID()", "!RECORDER!", "!WSA_TY_NM!", "!LOC_NM!"], 
                          ['', '', '', '', '', '', count_cb, guid_cb, '', '', ''])
        row_pairs = set()
        with arcpy.da.UpdateCursor("WeedSurveyData_fc", ["txBDate_fc", "newx", "newy", "txEDate_fc", "perim", "WSA_TY_NM", "srvytx_fc", "LOC_NM", "STATE_CD", "COUNTY_CD", "PARK_UNIT", "RECORDER", "TEAM", "CLIENT"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        wslfm = arcpy.FieldMappings()
        wslfm.addTable(Outgdb + "\\WeedSurveyLocation")
        arcpy.Append_management("WeedSurveyData_fc", Outgdb + "\\WeedSurveyLocation", "NO_TEST", wslfm)

        # Split out SCNTFC_CD fields
        add_and_calculate("WeedSurveyData_join2", ["txBDate", "txEDate", "txsrvy_me"], 
                          ["TEXT", "TEXT", "TEXT"], [30, 30, 50], 
                          ["!BEGIN_DT!", "!END_DT!", "!SRVY_ME!"], 
                          ['', '', ''])
        arcpy.DeleteField_management("WeedSurveyData_fc", "BEGIN_DT;END_DT;RECORDER;WSA_TY_NM;LOC_NM")
        surspfm = arcpy.FieldMappings()
        surspfm.addTable("WeedSurveyData_join2")
        surspfm.addTable("WeedSurveyData_fc")
        arcpy.CopyFeatures_management("WeedSurveyData_fc", workcopy + "\\WeedSurveyData_fc")
        arcpy.SpatialJoin_analysis("WeedSurveyData_join2", "WeedSurveyData_fc", "WeedSurveyData_spp", "JOIN_ONE_TO_MANY", "KEEP_COMMON", surspfm, "ARE_IDENTICAL_TO", "", "")
        with arcpy.da.UpdateCursor("WeedSurveyData_spp", "*", "\"txBDate\" <> \"txBDate_fc\" OR \"txEDate\" <> \"txEDate_fc\" OR \"RECORDER\" <> \"RECORDER_fc\" OR \"WSA_TY_NM\" <> \"WSA_TY_NM_fc\" OR \"LOC_NM\" <> \"LOC_NM_fc\" OR \"txsrvy_me\" <> \"srvytx_fc\"") as cursor:
            for row in cursor:
                cursor.deleteRow()
        species_append("WeedSurveyData", "SURV_GUID", "WEEDSURVEYSPECIES")
    
    # Set WeedInfestationData as workspace
    arcpy.env.workspace = workcopy + "\\WeedInfestationData"

    # Check for data in each feature class and project if needed
    arcpy.AddMessage("Processing weed infestation data.")
    project_albers_fc("WeedInfestationDataAlbers")
    
    # Buffer point and line data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("WeedInfestation")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "WeedInfestationData_allpy", "POLYGON", workcopy + "\\WeedInfestationData\\WeedInfestationPy", "", "", sralbers)
    WIPy = arcpy.ListFeatureClasses("WeedInfestation*Py_gcs")
    WIPyCt = len(WIPy)
    infpy = arcpy.FieldMappings()
    infpy.addTable(workcopy + "\\WeedInfestationData\\WeedInfestationPy")
    if WIPyCt > 0:
        arcpy.Append_management(WIPy, workcopy + "\\WeedInfestationData_allpy", "NO_TEST", infpy)
                
        # Calculate acreage
        add_and_calculate(workcopy + "\\WeedInfestationData_allpy", ["GRSACRE_ME", "NETACRE_ME", "newx", "newy", "CNTR_PT_CN"], 
                          ["DOUBLE", "DOUBLE", "DOUBLE", "DOUBLE", "TEXT"], [0, 0, 0, 0, 50], 
                          ["!SHAPE.AREA@ACRES!", "!GRSACRE_ME! * !EST_CVR_RT!/100", "!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], 
                          ['', '', '', '', ''])

        # Calculate State and County fields
        state_and_county("WeedInfestationData")
        add_and_calculate("WeedInfestationData_join", ["STATE_CD", "COUNTY_CD", "DELID"], 
                          ["TEXT", "TEXT", "LONG"], [2, 5, 0], 
                          ["!STUSPS_1!", "!GEOID_1!", "autoIncrement()"], 
                          ['', '', count_cb])

        # Calculate LGCY_FL
        arcpy.AddField_management("WeedInfestationData_join", "LGCY_FL", "TEXT", "", "", 1)
        arcpy.CalculateField_management("WeedInfestationData_join", "LGCY_FL", "\"" + LgcySt + "\"")

        # Convert UTC dates
        convert_utc_dates("WeedInfestationData", "BEGIN_DT", 0)

        # Append to WeedInfestationLocation
        add_and_calculate("WeedInfestationData_join2", ["rejoin_ct"], ["LONG"], [0], ["autoIncrement()"], [count_cb])
        arcpy.CopyFeatures_management("WeedInfestationData_join2", "WeedInfestation_fc")
        add_and_calculate("WeedInfestation_fc", ["txBDate", "perim", "cvrrttx", "infstntx", "netacretx", "grsacretx", "newxtx", "newytx"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 20, 20, 20, 20, 20, 20, 20], 
                          ["!BEGIN_DT!", "str(!SHAPE.LENGTH@METERS!)", "!EST_CVR_RT!", "!INFSTN_QY!", "!NETACRE_ME!", "!GRSACRE_ME!", "!newx!", "!newy!"], 
                          ['', '', '', '', '', '', '', ''])
        row_pairs = set()
        with arcpy.da.UpdateCursor("WeedInfestation_fc", ["cvrrttx", "QT_MTHD_TX", "infstntx", "netacretx", "QY_UOM_NM", "grsacretx", "txBDate", "PHNLGY_NM", "perim", "newx", "newy", "PHYSLMT_TX", "ACSMODE_NM", "SCNTFC_CD", "LOC_NM"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.Select_analysis("WeedInfestation_fc", "WeedInfestation_estcvrrt", "\"EST_CVR_RT\" > 0")
        arcpy.AddField_management("WeedInfestation_estcvrrt", "INF_GUID", "GUID")
        arcpy.CalculateField_management("WeedInfestation_estcvrrt", "INF_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        wilfm = arcpy.FieldMappings()
        wilfm.addTable(Outgdb + "\\WeedInfestationLocation")
        arcpy.Append_management("WeedInfestation_estcvrrt", Outgdb + "\\WeedInfestationLocation", "NO_TEST", wilfm)

        # Split out LU_CTGY_NM fields
        add_and_calculate("WeedInfestationData_join2", ["txBDate_jn2", "SCNTFC_CD_jn2", "cvrrttx_jn2"], 
                          ["TEXT", "TEXT", "TEXT"], [30, 10, 20], 
                          ["!BEGIN_DT!", "!SCNTFC_CD!", "!EST_CVR_RT!"], 
                          ['', '', ''])
        arcpy.DeleteField_management("WeedInfestationData_join2", "SCNTFC_CD")
        arcpy.AddField_management("WeedInfestation_estcvrrt", "rejoin_ct_1", "LONG")
        arcpy.CalculateField_management("WeedInfestation_estcvrrt", "rejoin_ct_1", "!rejoin_ct!", "PYTHON3")
        lufm = arcpy.FieldMappings()
        lufm.addTable("WeedInfestationData_join2")
        lufm.addTable("WeedInfestation_estcvrrt")
        arcpy.SpatialJoin_analysis("WeedInfestationData_join2", "WeedInfestation_estcvrrt", "WeedInfestation_lu", "JOIN_ONE_TO_MANY", "KEEP_ALL", lufm, "ARE_IDENTICAL_TO", "", "")
        with arcpy.da.UpdateCursor("WeedInfestation_lu", "*", "\"txBDate\" <> \"txBDate_jn2\" OR \"SCNTFC_CD\" <> \"SCNTFC_CD_jn2\" OR \"cvrrttx\" <> \"cvrrttx_jn2\"") as cursor:
            for row in cursor:
                cursor.deleteRow()
        LuNum = 1
        for field in arcpy.ListFields("WeedInfestation_lu", "LU_CTGY_NM*"):
            arcpy.Select_analysis("WeedInfestation_lu", "lutb2_" + str(LuNum), "\"" + field.name + "\"" + " <> \'\'")
            RecNum = arcpy.GetCount_management("lutb2_" + str(LuNum)).getOutput(0)
            if int(RecNum) > 0:
                arcpy.CalculateField_management("lutb2_" + str(LuNum), "LU_CTGY_NM", "!" + field.name + "!", "PYTHON3")
            LuNum += 1
        lufld = arcpy.ListFeatureClasses("lutb2_*")
        arcpy.CreateFeatureclass_management("memory", "WeedInfestation_copy", "POLYGON", "WeedInfestation_lu", "", "", new_spatialref)
        arcpy.Append_management(lufld, "WeedInfestation_copy", "NO_TEST")
        arcpy.Select_analysis("WeedInfestation_copy", "WeedInfestation_copy2", "\"LU_CTGY_NM\" IS NOT NULL")
        row_pairs = set()
        with arcpy.da.UpdateCursor("WeedInfestation_copy2", ["LU_CTGY_NM", "INF_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)        
        arcpy.CopyRows_management("WeedInfestation_copy2", "lutb_all")
        wichfm = arcpy.FieldMappings()
        wichfm.addTable(Outgdb + "\\ASSOCIATEDCHARACTERISTIC")
        arcpy.Append_management("lutb_all", Outgdb + "\\ASSOCIATEDCHARACTERISTIC", "NO_TEST", wichfm)

    # Set ProposedTreatmentData as workspace
    arcpy.env.workspace = workcopy + "\\ProposedTreatmentData"

    # Check for data in each Biological feature class and project if needed
    arcpy.CreateFeatureDataset_management(workcopy, "ProposedTreatmentDataUTM", new_spatialref)
    arcpy.AddMessage("Processing proposed biological treatment data.")
    for fc in arcpy.ListFeatureClasses("ProposedBiological*"):
        arcpy.RepairGeometry_management(fc)
        desc = arcpy.Describe(fc)
        arcpy.AddMessage(desc.name + " being processed.")
        fcct = arcpy.GetCount_management(fc).getOutput(0)
        if int(fcct) > 0:
            fld_spatialref = arcpy.Describe(fc).spatialReference
            if fld_spatialref != new_spatialref:
                arcpy.Project_management(fc, workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs", new_spatialref)              
            else:
                arcpy.CopyFeatures_management(fc, workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs")
            arcpy.CopyFeatures_management(workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs", "memory/" + fc + "_gcs")

    # Append all polygon files together
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("ProposedBiological")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "ProposedBioTreatment_allpy", "POLYGON", workcopy + "\\ProposedTreatmentData\\ProposedBiologicalTreatmentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("ProposedBiological*Py_gcs")
    PTPyCt = len(PTPy)
    pbiopy = arcpy.FieldMappings()
    pbiopy.addTable(workcopy + "\\ProposedTreatmentData\\ProposedBiologicalTreatmentPy")
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\ProposedBioTreatment_allpy", "NO_TEST", pbiopy)
            
        # Append to ProposedTreatmentLocation
        add_and_calculate(workcopy + "\\ProposedBioTreatment_allpy", ["rejoin_ct"], ["LONG"], [0], ["autoIncrement()"], [count_cb])
        arcpy.CopyFeatures_management(workcopy + "\\ProposedBioTreatment_allpy", "ProposedBioTreatment_fc")
        add_and_calculate("ProposedBioTreatment_fc", ["txPDate", "newx", "newy", "perim", "applyrtx", "pracreqytx", "nrappltx", "timeframetx"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 20, 20, 20, 20, 20, 20, 20], 
                          ["!PRP_DATE!", "str(!SHAPE.CENTROID.X!)", "str(!SHAPE.CENTROID.Y!)", "str(!SHAPE.LENGTH@METERS!)", "!APPL_YR_QY!", "!PR_ACRE_QY!", "!NR_APPL!", "!TIMEFRAME!"], 
                          ['', '', '', '', '', '', '', ''])
        row_pairs = set()
        with arcpy.da.UpdateCursor("ProposedBioTreatment_fc", ["newx", "newy", "perim", "applyrtx", "PRP_TX", "pracreqytx", "PUP_NR", "BCP_NR", "nrappltx", "LOC_NM", "timeframetx", "txPDate", "RLSITE_TX", "CAUTION_TX", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "CO_CM_TX", "DIR_CM_TX"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("ProposedBioTreatment_fc", "PROP_TRT_GUID", "GUID")
        arcpy.CalculateField_management("ProposedBioTreatment_fc", "PROP_TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        pbtfm = arcpy.FieldMappings()
        pbtfm.addTable(Outgdb + "\\ProposedTreatmentLocation")
        arcpy.Append_management("ProposedBioTreatment_fc", Outgdb + "\\ProposedTreatmentLocation", "NO_TEST", pbtfm)

        # Split out SCNTFC_CD fields
        arcpy.AddField_management("ProposedBioTreatment_fc", "rejoin_ct_1", "LONG")
        arcpy.CalculateField_management("ProposedBioTreatment_fc", "rejoin_ct_1", "!rejoin_ct!", "PYTHON3")
        pbiofm = arcpy.FieldMappings()
        pbiofm.addTable(workcopy + "\\ProposedBioTreatment_allpy")
        pbiofm.addTable("ProposedBioTreatment_fc")
        arcpy.SpatialJoin_analysis(workcopy + "\\ProposedBioTreatment_allpy", "ProposedBioTreatment_fc", "ProposedBioTreatmentData_pbio", "JOIN_ONE_TO_MANY", "KEEP_COMMON", pbiofm, "ARE_IDENTICAL_TO", "", "")
        arcpy.CopyFeatures_management("ProposedBioTreatmentData_pbio", "ProposedBioTreatmentData_spp")
        SppNum = 1
        species_append("ProposedBioTreatmentData", "PROP_TRT_GUID", "PROPOSALSPECIES")
    
        # Split out BIO_SCNTFC_CD fields
        arcpy.CopyFeatures_management("ProposedBioTreatment_fc", "ProposedBioTreatmentData_pbiotb2")
        for field in arcpy.ListFields("ProposedBioTreatmentData_pbiotb2", "BIO_SCNTFC_CD_1*"):
            arcpy.DeleteField_management("ProposedBioTreatmentData_pbiotb2", "\"" + field.name + "\"")
        BsppNum = 1
        for field in arcpy.ListFields("ProposedBioTreatmentData_pbiotb2", "BIO_SCNTFC_CD*"):
            arcpy.Select_analysis("ProposedBioTreatmentData_pbiotb2", "pbiotb4_" + str(BsppNum), "\"" + field.name + "\"" + " IS NOT NULL")            
            RecNum = arcpy.GetCount_management("pbiotb4_" + str(BsppNum)).getOutput(0)
            if int(RecNum) > 0:
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "BIO_SCNTFC_CD", "!" + field.name + "!", "PYTHON3")
                BioNum = str(field.name)
                BioNum = BioNum.strip("BIO_SCNTFC_CD")
                BioUse = str("SPC_USE_QY" + BioNum)
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "SPC_USE_QY", "!" + BioUse + "!", "PYTHON3")
                BioMat = str("HSTMATL_NM" + BioNum)
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "HSTMATL_NM", "!" + BioMat + "!", "PYTHON3")
                BioPDt = str("PRMT_DT" + BioNum)
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "PRMT_DT", "!" + BioPDt + "!", "PYTHON3")
                BioPRq = str("PRMTREQ_FL" + BioNum)
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "PRMTREQ_FL", "!" + BioPRq + "!", "PYTHON3")
                BioLCy = str("LFCYCLE_NM" + BioNum)
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "LFCYCLE_NM", "!" + BioLCy + "!", "PYTHON3")
                BioCty = str("CLLCNTY_NM" + BioNum)
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "CLLCNTY_NM", "!" + BioCty + "!", "PYTHON3")
                BioSta = str ("CLSTATE_CD" + BioNum)
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "CLSTATE_CD", "!" + BioSta + "!", "PYTHON3")
                BioPmt = str("PRMT_NR" + BioNum)
                arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "PRMT_NR", "!" + BioPmt + "!", "PYTHON3")
                BsppNum += 1
        bsppfld = arcpy.ListFeatureClasses("pbiotb4_*")
        arcpy.Append_management(bsppfld, "ProposedBioTreatmentData_pbiotb2", "NO_TEST")
        arcpy.Select_analysis("ProposedBioTreatmentData_pbiotb2", "ProposedBioTreatmentData_pbiotb2sel", "\"BIO_SCNTFC_CD\" IS NOT NULL")
        bsppcnt = arcpy.GetCount_management("ProposedBioTreatmentData_pbiotb2sel").getOutput(0)
        if int(bsppcnt) > 0:
            row_pairs = set()
            with arcpy.da.UpdateCursor("ProposedBioTreatmentData_pbiotb2sel", ["BIO_SCNTFC_CD", "PROP_TRT_GUID"]) as cursor:
                for row in cursor:
                    row_pair = tuple(row)
                    if row_pair in row_pairs:
                        cursor.deleteRow()
                    else:
                        row_pairs.add(row_pair)
            arcpy.CopyRows_management("ProposedBioTreatmentData_pbiotb2sel", "pbiotb_all")
            pbtbiofm = arcpy.FieldMappings()
            pbtbiofm.addTable(Outgdb + "\\PROPOSALBIOCOMPONENTAGENT")
            arcpy.Append_management("pbiotb_all", Outgdb + "\\PROPOSALBIOCOMPONENTAGENT", "NO_TEST", pbtbiofm)
        
        # Split out COOP_PERS fields
        coop_pers_append("ProposedBioTreatment")
        
        # Split out NEPA_NR fields
        nepa_append("ProposedBioTreatment")

    # Check for data in each Chemical feature class and project if needed
    arcpy.env.workspace = workcopy + "\\ProposedTreatmentData"
    arcpy.AddMessage("Processing proposed chemical treatment data.")
    for fc in arcpy.ListFeatureClasses("ProposedChemical*"):
        desc = arcpy.Describe(fc)
        arcpy.AddMessage(desc.name + " being processed.")
        fcct = arcpy.GetCount_management(fc).getOutput(0)
        if int(fcct) > 0:
            fld_spatialref = arcpy.Describe(fc).spatialReference
            if fld_spatialref != new_spatialref:
                arcpy.Project_management(fc, workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs", new_spatialref)           
            else:
                arcpy.CopyFeatures_management(fc, workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs")
            arcpy.CopyFeatures_management(workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs", "memory/" + fc + "_gcs")

    # Buffer point and line data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("ProposedChemical")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "ProposedChemTreatment_allpy", "POLYGON", workcopy + "\\ProposedTreatmentData\\ProposedChemicalTreatmentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("ProposedChemical*Py_gcs")
    PTPyCt = len(PTPy)
    pchempy = arcpy.FieldMappings()
    pchempy.addTable(workcopy + "\\ProposedTreatmentData\\ProposedChemicalTreatmentPy")    
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\ProposedChemTreatment_allpy", "NO_TEST", pchempy)

        # Append to ProposedTreatmentLocation
        add_and_calculate(workcopy + "\\ProposedChemTreatment_allpy", ["rejoin_ct"], ["LONG"], [0], ["autoIncrement()"], [count_cb])
        arcpy.CopyFeatures_management(workcopy + "\\ProposedChemTreatment_allpy", "ProposedChemTreatment_fc")  
        add_and_calculate("ProposedChemTreatment_fc", ["txPDate", "newx", "newy", "perim", "applyrtx", "pracreqytx", "nrappltx", "timeframetx"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 20, 20, 20, 20, 20, 20, 20], 
                          ["!PRP_DATE!", "str(!SHAPE.CENTROID.X!)", "str(!SHAPE.CENTROID.Y!)", "str(!SHAPE.LENGTH@METERS!)", "!APPL_YR_QY!", "!PR_ACRE_QY!", "!NR_APPL!", "!TIMEFRAME!"], 
                          ['', '', '', '', '', '', '', ''])
        row_pairs = set()
        with arcpy.da.UpdateCursor("ProposedChemTreatment_fc", ["newx", "newy", "perim", "applyrtx","PRP_TX", "pracreqytx", "PUP_NR", "nrappltx", "LOC_NM", "timeframetx", "txPDate", "NONTRGT_TX", "IPM_TX", "DPS_TX", "DLVR_NM", "PTTRN_NM","ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("ProposedChemTreatment_fc", "PROP_TRT_GUID", "GUID")
        arcpy.CalculateField_management("ProposedChemTreatment_fc", "PROP_TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        pctfm = arcpy.FieldMappings()
        pctfm.addTable(Outgdb + "\\ProposedTreatmentLocation")
        arcpy.CopyFeatures_management("ProposedChemTreatment_fc", Newgdb + "\\ProposedTreatmentLocation_fc")
        arcpy.Append_management(Newgdb + "\\ProposedTreatmentLocation_fc", Outgdb + "\\ProposedTreatmentLocation", "NO_TEST")
        
        # Split out SCNTFC_CD fields
        pchmfm = arcpy.FieldMappings()
        pchmfm.addTable(workcopy + "\\ProposedChemTreatment_allpy")
        arcpy.AddField_management("ProposedChemTreatment_fc", "rejoin_ct_1", "LONG")
        arcpy.CalculateField_management("ProposedChemTreatment_fc", "rejoin_ct_1", "!rejoin_ct!", "PYTHON3")
        arcpy.SpatialJoin_analysis(workcopy + "\\ProposedChemTreatment_allpy", "ProposedChemTreatment_fc", "ProposedChemTreatmentData_pchemtb", "JOIN_ONE_TO_MANY", "KEEP_COMMON", "APPL_YR_QY \"Duration of Proposal\" true true false 4 Long 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,APPL_YR_QY,-1,-1;PRP_TX \"Comments\" true true false 200 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PRP_TX,-1,-1;PR_ACRE_QY \"Estimated Treated Acres\" true true false 8 Double 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PR_ACRE_QY,-1,-1;PUP_NR \"Pesticide Use Proposal Number\" true true false 20 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PUP_NR,-1,-1;TEAM \"Team Code\" true false false 20 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,TEAM,-1,-1;PARK_UNIT \"Park Unit Code\" true false false 4 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PARK_UNIT,-1,-1;NR_APPL \"Number Applications\" true true false 2 Short 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,NR_APPL,-1,-1;LOC_NM \"Location Name\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,LOC_NM,-1,-1;TIMEFRAME \"Timeframe\" true true false 20 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,TIMEFRAME,-1,-1;PRP_DATE \"Proposal Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PRP_DATE,-1,-1;NONTRGT_TX \"Non Target Vegetation\" true true false 200 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,NONTRGT_TX,-1,-1;IPM_TX \"Integrated Pest Management\" true true false 200 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,IPM_TX,-1,-1;DPS_TX \"Desired Plant Species\" true true false 200 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,DPS_TX,-1,-1;DLVR_NM \"Delivery Method\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,DLVR_NM,-1,-1;PTTRN_NM \"Treatment Coverage Pattern Name\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PTTRN_NM,-1,-1;ORIG_LE \"Originator LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,ORIG_LE,-1,-1;ORIG_APPDT \"Originator Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,ORIG_APPDT,-1,-1;REVIEWER_LE \"Reviewer LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,REVIEWER_LE,-1,-1;REV_APPCD \"Reviewer Approval Code\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,REV_APPCD,-1,-1;REV_APPDT \"Reviewer Approval Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,REV_APPDT,-1,-1;PARK_LE \"Park LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PARK_LE,-1,-1;PARK_APPCD \"Park Approval Code\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PARK_APPCD,-1,-1;PARK_APPDT \"Park Approval Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PARK_APPDT,-1,-1;ST_COORD_LE \"State Coordinator LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,ST_COORD_LE,-1,-1;COOR_APPCD \"State Coordinator Approval Code\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,COOR_APPCD,-1,-1;COOR_APPDT \"State Coordinator Approval Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,COOR_APPDT,-1,-1;ST_DIR_LE \"Deputy State Director LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,ST_DIR_LE,-1,-1;DIR_APPCD \"Deputy State Director Approval Code\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,DIR_APPCD,-1,-1;DIR_APPDT \"Deputy State Director Approval Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,DIR_APPDT,-1,-1;ORIG_CM_TX \"Originator Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,ORIG_CM_TX,-1,-1;REV_CM_TX \"Reviewer Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,REV_CM_TX,-1,-1;PARK_CM_TX \"Park Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,PARK_CM_TX,-1,-1;CO_CM_TX \"State Coordinator Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,CO_CM_TX,-1,-1;DIR_CM_TX \"Deputy State Director Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,DIR_CM_TX,-1,-1;COOP_PERS \"Cooperator\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,COOP_PERS,-1,-1;SCNTFC_CD \"Scientific Name Code\" true false false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,SCNTFC_CD,-1,-1;SCNTFC_CD2 \"Scientific Name Code 2\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,SCNTFC_CD2,-1,-1;SCNTFC_CD3 \"Scientific Name Code 3\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,SCNTFC_CD3,-1,-1;SCNTFC_CD4 \"Scientific Name Code 4\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,SCNTFC_CD4,-1,-1;SCNTFC_CD5 \"Scientific Name Code 5\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,SCNTFC_CD5,-1,-1;NEPA_NR \"NEPA Reference Number\" true true false 30 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,NEPA_NR,-1,-1;TRADE_NM \"Trade Name\" true false false 40 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,TRADE_NM,-1,-1;MNFCTR_NM \"Manufacturer\" true true false 30 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,MNFCTR_NM,-1,-1;SITE_TX \"Release Site\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,SITE_TX,-1,-1;APP_RT_TX \"Application Rate from Label\" true true false 30 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,APP_RT_TX,-1,-1;APP_AMT_LOW \"Application Amount - Low\" true true false 8 Double 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,APP_AMT_LOW,-1,-1;APP_AMT_HIGH \"Application Amount - High\" true true false 8 Double 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,APP_AMT_HIGH,-1,-1;TRT_ID \"Overseer LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,TRT_ID,-1,-1;ROLE_NM \"Role Name\" true true false 20 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,ROLE_NM,-1,-1;CERT_NR \"License Number\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,CERT_NR,-1,-1;TRADE_NM2 \"Trade Name 2\" true true false 40 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,TRADE_NM2,-1,-1;MNFCTR_NM2 \"Manufacturer 2\" true true false 30 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,MNFCTR_NM2,-1,-1;APP_RT_TX2 \"Application Rate from Label 2\" true true false 30 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,APP_RT_TX2,-1,-1;APP_AMT_LOW2 \"Application Amount - Low 2\" true true false 8 Double 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,APP_AMT_LOW2,-1,-1;APP_AMT_HIGH2 \"Aplication Amount - High 2\" true true false 8 Double 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,APP_AMT_HIGH2,-1,-1;DelID \"DelID\" true true false 4 Long 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_allpy,DelID,-1,-1;TEAM_1 \"Team Code\" true false false 20 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_fc,TEAM,-1,-1;PARK_UNIT_1 \"Park Unit Code\" true false false 4 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_fc,PARK_UNIT,-1,-1;PRP_DATE_1 \"Proposal Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_fc,PRP_DATE,-1,-1;ORIG_LE_1 \"Originator LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_fc,ORIG_LE,-1,-1;ORIG_APPDT_1 \"Originator Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_fc,ORIG_APPDT,-1,-1;DelID_1 \"DelID\" true true false 4 Long 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_fc,DelID,-1,-1;PROP_TRT_GUID \"PROP_TRT_GUID\" true true false 38 Guid 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedChemTreatment_fc,PROP_TRT_GUID,-1,-1", "ARE_IDENTICAL_TO", "", "")
        arcpy.CopyFeatures_management("ProposedChemTreatmentData_pchemtb", "ProposedChemTreatmentData_spp")
        SppNum = 1
        species_append("ProposedChemTreatmentData", "PROP_TRT_GUID", "PROPOSALSPECIES")
                
        # Split out TRADE_NM fields
        arcpy.CopyFeatures_management("ProposedChemTreatmentData_pchemtb", "ProposedChemTreatmentData_pchemtb3")
        HerbNum = 1
        for field in arcpy.ListFields("ProposedChemTreatmentData_pchemtb3", "TRADE_NM*"):
            arcpy.Select_analysis("ProposedChemTreatmentData_pchemtb3", "pchemtb4_" + str(HerbNum), "\"" + field.name + "\"" + " IS NOT NULL")
            RecNum = arcpy.GetCount_management("pchemtb4_" + str(HerbNum)).getOutput(0)
            if int(RecNum) > 0:
                arcpy.CalculateField_management("pchemtb4_" + str(HerbNum), "TRADE_NM", "!" + field.name + "!", "PYTHON3")
                ChemNum = str(field.name)
                ChemNum = ChemNum.strip("TRADE_NM")
                ChemMfr = str("MNFCTR_NM" + ChemNum)
                arcpy.CalculateField_management("pchemtb4_" + str(HerbNum), "MNFCTR_NM", "!" + ChemMfr + "!", "PYTHON3")
                ChemRt = str("APP_RT_TX" + ChemNum)
                arcpy.CalculateField_management("pchemtb4_" + str(HerbNum), "APP_RT_TX", "!" + ChemRt + "!", "PYTHON3")
                ChemLow = str("APP_AMT_LOW" + ChemNum)
                arcpy.CalculateField_management("pchemtb4_" + str(HerbNum), "APP_AMT_LOW", "!" + ChemLow + "!", "PYTHON3")
                ChemHi = str("APP_AMT_HIGH" + ChemNum)
                arcpy.CalculateField_management("pchemtb4_" + str(HerbNum), "APP_AMT_HIGH", "!" + ChemHi + "!", "PYTHON3")
                HerbNum += 1
        herbfld = arcpy.ListFeatureClasses("pchemtb4_*")
        arcpy.Append_management(herbfld, "ProposedChemTreatmentData_pchemtb3")
        arcpy.Select_analysis("ProposedChemTreatmentData_pchemtb3", "ProposedChemTreatmentData_pchemtb3sel", "\"TRADE_NM\" IS NOT NULL")
        herbcnt = arcpy.GetCount_management("ProposedChemTreatmentData_pchemtb3sel").getOutput(0)
        if int(herbcnt) > 0:
            row_pairs = set()
            with arcpy.da.UpdateCursor("ProposedChemTreatmentData_pchemtb3sel", ["TRADE_NM", "PROP_TRT_GUID"]) as cursor:
                for row in cursor:
                    row_pair = tuple(row)
                    if row_pair in row_pairs:
                        cursor.deleteRow()
                    else:
                        row_pairs.add(row_pair)
            arcpy.CopyRows_management("ProposedChemTreatmentData_pchemtb3sel", "pchemtb_all")
            pctchfm = arcpy.FieldMappings()
            pctchfm.addTable(Outgdb + "\\PROPOSALCHEMCOMPCONTROLAGENT")
            arcpy.Append_management("pchemtb_all", Outgdb + "\\PROPOSALCHEMCOMPCONTROLAGENT", "NO_TEST", pctchfm)
        
        # Split out COOP_PERS fields
        coop_pers_append("ProposedChemTreatment")
        
        # Split out NEPA_NR fields
        nepa_append("ProposedChemTreatment")
        
    # Check for data in each Other feature class
    arcpy.env.workspace = workcopy + "\\ProposedTreatmentData"
    arcpy.AddMessage("Processing proposed other treatment data.")
    for fc in arcpy.ListFeatureClasses("ProposedOther*"):
        arcpy.RepairGeometry_management(fc)
        desc = arcpy.Describe(fc)
        arcpy.AddMessage(desc.name + " being processed.")       
        fcct = arcpy.GetCount_management(fc).getOutput(0)
        if int(fcct) > 0:
            fld_spatialref = arcpy.Describe(fc).spatialReference
            if fld_spatialref != new_spatialref:
                arcpy.Project_management(fc, workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs", new_spatialref)             
            else:
                arcpy.CopyFeatures_management(fc, workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs")
            arcpy.CopyFeatures_management(workcopy + "\\ProposedTreatmentDataUTM\\" + fc + "_gcs", "memory/" + fc + "_gcs")

    # Buffer point and line data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("ProposedOther")   

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "ProposedOthTreatment_allpy", "POLYGON", workcopy + "\\ProposedTreatmentData\\ProposedOtherTreatmentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("ProposedOther*Py_gcs")
    PTPyCt = len(PTPy)
    pothpy = arcpy.FieldMappings()
    pothpy.addTable(workcopy + "\\ProposedTreatmentData\\ProposedOtherTreatmentPy") 
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\ProposedOthTreatment_allpy", "NO_TEST", pothpy)

        # Append to ProposedTreatmentLocation
        add_and_calculate(workcopy + "\\ProposedOthTreatment_allpy", ["rejoin_ct"], ["LONG"], [0], ["autoIncrement()"], [count_cb])
        arcpy.CopyFeatures_management(workcopy + "\\ProposedOthTreatment_allpy", "ProposedOthTreatment_fc")
        add_and_calculate("ProposedOthTreatment_fc", ["txPDate", "newx", "newy", "perim", "applyrtx", "pracreqytx", "nrappltx", "timeframetx"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 20, 20, 20, 20, 20, 20, 20], 
                          ["!PRP_DATE!", "str(!SHAPE.CENTROID.X!)", "str(!SHAPE.CENTROID.Y!)", "str(!SHAPE.LENGTH@METERS!)", "!APPL_YR_QY!", "!PR_ACRE_QY!", "!NR_APPL!", "!TIMEFRAME!"], 
                          ['', '', '', '', '', '', '', ''])       
        row_pairs = set()
        with arcpy.da.UpdateCursor("ProposedOthTreatment_fc", ["newx", "newy", "perim", "applyrtx","PRP_TX", "pracreqytx", "nrappltx", "LOC_NM", "timeframetx", "txPDate", "NONTRGT_TX", "IPM_TX", "DPS_TX","ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "CO_CM_TX", "DIR_CM_TX"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("ProposedOthTreatment_fc", "PROP_TRT_GUID", "GUID")
        arcpy.CalculateField_management("ProposedOthTreatment_fc", "PROP_TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        potfm = arcpy.FieldMappings()
        potfm.addTable(Outgdb + "\\ProposedTreatmentLocation")
        arcpy.Append_management("ProposedOthTreatment_fc", Outgdb + "\\ProposedTreatmentLocation", "NO_TEST", potfm)
        
        # Split out SCNTFC_CD fields
        pothfm = arcpy.FieldMappings()
        pothfm.addTable(workcopy + "\\ProposedOthTreatment_allpy")
        arcpy.AddField_management("ProposedOthTreatment_fc", "rejoin_ct_1", "LONG")
        arcpy.CalculateField_management("ProposedOthTreatment_fc", "rejoin_ct_1", "!rejoin_ct!", "PYTHON3")
        arcpy.SpatialJoin_analysis(workcopy + "\\ProposedOthTreatment_allpy", "ProposedOthTreatment_fc", "ProposedOthTreatmentData_poth", "JOIN_ONE_TO_MANY", "KEEP_COMMON", "APPL_YR_QY \"Duration of Proposal\" true true false 4 Long 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,APPL_YR_QY,-1,-1;PRP_TX \"Comments\" true true false 200 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,PRP_TX,-1,-1;PR_ACRE_QY \"Estimated Treated Acres\" true true false 8 Double 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,PR_ACRE_QY,-1,-1;TEAM \"Team Code\" true false false 20 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,TEAM,-1,-1;PARK_UNIT \"Park Unit Code\" true false false 4 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,PARK_UNIT,-1,-1;NR_APPL \"Number Applications\" true true false 2 Short 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,NR_APPL,-1,-1;LOC_NM \"Location Name\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,LOC_NM,-1,-1;TIMEFRAME \"Timeframe\" true true false 20 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,TIMEFRAME,-1,-1;PRP_DATE \"Proposal Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,PRP_DATE,-1,-1;NONTRGT_TX \"Non Target Vegetation\" true true false 200 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,NONTRGT_TX,-1,-1;IPM_TX \"Integrated Pest Management\" true true false 200 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,IPM_TX,-1,-1;DPS_TX \"Desired Plant Species\" true true false 200 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,DPS_TX,-1,-1;ORIG_LE \"Originator LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,ORIG_LE,-1,-1;ORIG_APPDT \"Originator Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,ORIG_APPDT,-1,-1;REVIEWER_LE \"Reviewer LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,REVIEWER_LE,-1,-1;REV_APPCD \"Reviewer Approval Code\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,REV_APPCD,-1,-1;REV_APPDT \"Reviewer Approval Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,REV_APPDT,-1,-1;PARK_LE \"Park LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,PARK_LE,-1,-1;PARK_APPCD \"Park Approval Code\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,PARK_APPCD,-1,-1;PARK_APPDT \"Park Approval Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,PARK_APPDT,-1,-1;ST_COORD_LE \"State Coordinator LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,ST_COORD_LE,-1,-1;COOR_APPCD \"State Coordinator Approval Code\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,COOR_APPCD,-1,-1;COOR_APPDT \"State Coordinator Approval Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,COOR_APPDT,-1,-1;ST_DIR_LE \"Deputy State Director LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,ST_DIR_LE,-1,-1;DIR_APPCD \"Deputy State Director Approval Code\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,DIR_APPCD,-1,-1;DIR_APPDT \"Deputy State Director Approval Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,DIR_APPDT,-1,-1;ORIG_CM_TX \"Originator Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,ORIG_CM_TX,-1,-1;REV_CM_TX \"Reviewer Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,REV_CM_TX,-1,-1;PARK_CM_TX \"Park Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,PARK_CM_TX,-1,-1;CO_CM_TX \"State Coordinator Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,CO_CM_TX,-1,-1;DIR_CM_TX \"Deputy State Director Comment\" true true false 100 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,DIR_CM_TX,-1,-1;COOP_PERS \"Cooperator\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,COOP_PERS,-1,-1;SCNTFC_CD \"Scientific Name Code\" true false false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,SCNTFC_CD,-1,-1;SCNTFC_CD2 \"Scientific Name Code 2\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,SCNTFC_CD2,-1,-1;SCNTFC_CD3 \"Scientific Name Code 3\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,SCNTFC_CD3,-1,-1;SCNTFC_CD4 \"Scientific Name Code 4\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,SCNTFC_CD4,-1,-1;SCNTFC_CD5 \"Scientific Name Code 5\" true true false 10 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,SCNTFC_CD5,-1,-1;NEPA_NR \"NEPA Reference Number\" true true false 30 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,NEPA_NR,-1,-1;DelID \"DelID\" true true false 4 Long 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_allpy,DelID,-1,-1;TEAM_1 \"Team Code\" true false false 20 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_fc,TEAM,-1,-1;PARK_UNIT_1 \"Park Unit Code\" true false false 4 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_fc,PARK_UNIT,-1,-1;PRP_DATE_1 \"Proposal Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_fc,PRP_DATE,-1,-1;ORIG_LE_1 \"Originator LE ID\" true true false 50 Text 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_fc,ORIG_LE,-1,-1;ORIG_APPDT_1 \"Originator Date\" true true false 8 Date 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_fc,ORIG_APPDT,-1,-1;DelID_1 \"DelID\" true true false 4 Long 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_fc,DelID,-1,-1;PROP_TRT_GUID \"PROP_TRT_GUID\" true true false 38 Guid 0 0 ,First,#,C:\\NISIMS\\NISIMS_File_Structure\\NISIMS\\Data\\Spatial_Data\\NISIMS_Field\\workcopy.gdb\\ProposedTreatmentDataUTM\\ProposedOthTreatment_fc,PROP_TRT_GUID,-1,-1", "ARE_IDENTICAL_TO", "", "")
        arcpy.CopyFeatures_management("ProposedOthTreatmentData_poth", "ProposedOthTreatmentData_spp")
        SppNum = 1
        species_append("ProposedOthTreatmentData", "PROP_TRT_GUID", "PROPOSALSPECIES")
    
        # Split out COOP_PERS fields
        coop_pers_append("ProposedOthTreatment")
        
        # Split out NEPA_NR fields
        nepa_append("ProposedChemTreatment")
        
    # Create projection datasets
    arcpy.env.workspace = workcopy + "\\TreatmentData"
    arcpy.CreateFeatureDataset_management(workcopy, "TreatmentDataUTM", new_spatialref)
    arcpy.CreateFeatureDataset_management(workcopy, "TreatmentDataAlbers", sralbers)

    # Check for data in each Biological feature class    
    arcpy.AddMessage("Processing biological treatment data.")
    project_albers_treat("Biological")

    # Buffer point and line data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("Biological")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "BiologicalTreatment_allpy", "POLYGON", workcopy + "\\TreatmentData\\BiologicalComponentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("Biological*Py_gcs")
    PTPyCt = len(PTPy)
    biopy = arcpy.FieldMappings()
    biopy.addTable(workcopy + "\\TreatmentData\\BiologicalComponentPy")    
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\BiologicalTreatment_allpy", "NO_TEST", biopy)

        # Calculate State and County fields
        add_and_calculate(workcopy + "\\BiologicalTreatment_allpy", ["newx", "newy", "CNTR_PT_CN"], ["DOUBLE", "DOUBLE", "TEXT"], [0, 0, 50], ["!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], ['', '', ''])
        state_and_county(BiologicalTreatment)
        add_and_calculate("BiologicalTreatment_join", ["STATE_CD", "COUNTY_CD"], ["TEXT", "TEXT"], [2, 5], ["!STUSPS_1!", "!GEOID_1!"], ['', ''])  
            
        # Convert UTC dates
        convert_utc_dates("BiologicalTreatment", "TRT_BEG_DT", "TRT_END_DT")

        # Calculate acreages
        calculate_treat_acres("BiologicalTreatment")
        
        # Calculate LGCY_FL
        arcpy.AddField_management("BiologicalTreatment_utm2", "LGCY_FL", "TEXT", "", "", 1)
        arcpy.CalculateField_management("BiologicalTreatment_utm2", "LGCY_FL", "\"" + LgcySt + "\"", "PYTHON3")

        # Calculate CMP_TY_NM
        arcpy.AddField_management("BiologicalTreatment_utm2", "CMP_TY_NM", "TEXT", "", "", 20)
        arcpy.CalculateField_management("BiologicalTreatment_utm2", "CMP_TY_NM", "\"BIOLOGICAL\"")

        # Append to TreatmentComponentLocation
        add_and_calculate("BiologicalTreatment_utm2", ["txBDate"], ["TEXT"], [30], ["!TRT_BEG_DT!"], [''])
        arcpy.CopyFeatures_management("BiologicalTreatment_utm2", "BiologicalTreatment_fc")
        add_and_calculate("BiologicalTreatment_fc", ["txEDate", "txColDt", "perim", "spcusetx", "temptx", "wndtx", "newxtx", "newytx", "clcacretx_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 30, 20, 20, 20, 20, 20, 20, 20], 
                          ["!TRT_END_DT!", "!COLLECT_DT!", "str(!SHAPE.LENGTH@METERS!)", "!SPC_USE_QY!", "!FA_AIR_ME!", "!WNDMPH_ME!", "!newx!", "!newy!", "!CLCACRE_ME!"], 
                          ['', '', '', '', '', '', '', '', '']) 
        row_pairs = set()
        with arcpy.da.UpdateCursor("BiologicalTreatment_fc", ["AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "txBDate", "txEDate", "PHNLGY_NM", "DPC_TX", "BUP_NR", "BIO_SCNTFC_CD", "spcusetx", "PRTCMTH_TX", "RLSDRCT_TX", "SOURCE", "HSTMATL_NM", "LFCYCLE_NM", "CLLCNTY_NM", "txColDt", "CLSTATE_CD", "temptx", "wndtx", "SL_MOIS_NM", "WNDDRCT_CD", "newx", "newy", "perim", "clcacretx_fc", "NOTES"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("BiologicalTreatment_fc", "TRT_GUID", "GUID")
        arcpy.CalculateField_management("BiologicalTreatment_fc", "TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        biofm = arcpy.FieldMappings()
        biofm.addTable(Outgdb + "\\TreatmentComponentLocation")
        arcpy.Append_management("BiologicalTreatment_fc", Outgdb + "\\TreatmentComponentLocation", "NO_TEST", biofm)

        # Merge to BIOLOGICALCOMPONENT
        add_and_calculate("BiologicalTreatment_fc", ["BIO_SCNTFC_CD_fc", "txBDate_fc", "spcusetx_fc"], 
                          ["TEXT", "TEXT", "TEXT"], [10, 30, 20], 
                          ["!BIO_SCNTFC_CD!", "!txBDate!", "!spcusetx!"], 
                          ['', '', '']) 
        add_and_calculate("BiologicalTreatment_utm2", ["clcacretx"], ["TEXT"], [20], ["!CLCACRE_ME!"], [''])
        biotbfm = arcpy.FieldMappings()
        biotbfm.addTable("BiologicalTreatment_utm2")
        biotbfm.addTable("BiologicalTreatment_fc")
        arcpy.SpatialJoin_analysis("BiologicalTreatment_utm2", "BiologicalTreatment_fc", "BiologicalTreatmentData_spp", "JOIN_ONE_TO_MANY", "KEEP_COMMON", biotbfm, "ARE_IDENTICAL_TO", "", "")       
        with arcpy.da.UpdateCursor("BiologicalTreatmentData_spp", "*", "\"BIO_SCNTFC_CD\" <> \"BIO_SCNTFC_CD_fc\" OR \"txBDate\" <> \"txBDate_fc\" OR \"spcusetx\" <> \"spcusetx_fc\" OR \"clcacretx\" <> \"clcacretx_fc\"") as cursor:
            for row in cursor:
                cursor.deleteRow()
        row_pairs = set()
        with arcpy.da.UpdateCursor("BiologicalTreatmentData_spp", ["BIO_SCNTFC_CD", "TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management("BiologicalTreatmentData_spp", "biotb_all")
        biocompfm = arcpy.FieldMappings()
        biocompfm.addTable(Outgdb + "\\BIOLOGICALCOMPONENT")
        arcpy.Append_management("biotb_all", Outgdb + "\\BIOLOGICALCOMPONENT", "NO_TEST", biocompfm)

        # Split out SCNTFC_CD fields
        SppNum = 1
        treat_species_append("BiologicalTreatmentData")

        # Calculate net acreage for BIOLOGICALCOMPONENT table
        arcpy.JoinField_management(Outgdb + "\\BIOLOGICALCOMPONENT", "TRT_GUID", "BiologicalTreatmentData_cvrsum", "TRT_GUID", ["SUM_EST_CVR_RT", "CLCACRE_ME"])
        arcpy.CalculateField_management(Outgdb + "\\BIOLOGICALCOMPONENT", "CVRAREA_ME", "accalc(!CVRAREA_ME!,!SUM_EST_CVR_RT!,!CLCACRE_ME!)", "PYTHON3", trtac_cb)
        arcpy.DeleteField_management(Outgdb + "\\BIOLOGICALCOMPONENT", "SUM_EST_CVR_RT;CLCACRE_ME;SUM_EST_CVR_RT_1;CLCACRE_ME_1")
    
    # Check for data in each Chemical feature class
    arcpy.env.workspace = workcopy + "\\TreatmentData"
    arcpy.AddMessage("Processing chemical treatment data.")
    project_albers_treat("Chemical")
    
    # Buffer line and point data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("Chemical")

    # Remove non-zeroes
    remove_nonzeroes("Chemical", "AGT_APP_RT2", "TRADE_NM2")
    remove_nonzeroes("Chemical", "ADJ_ACTLUSE_QTY", "ADJ_TRADE_NM")
    remove_nonzeroes("Chemical", "ADJ_AGT_APP_RT", "ADJ_TRADE_NM")
    remove_nonzeroes("Chemical", "ADJ_ACTLUSE_QTY2", "ADJ_TRADE_NM2")
    remove_nonzeroes("Chemical", "ADJ_AGT_APP_RT2", "ADJ_TRADE_NM2")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "ChemicalTreatment_allpy", "POLYGON", workcopy + "\\TreatmentData\\ChemicalComponentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("Chemical*Py_gcs")
    PTPyCt = len(PTPy)
    chempy = arcpy.FieldMappings()
    chempy.addTable(workcopy + "\\TreatmentData\\ChemicalComponentPy")
    if int(PTPyCt) > 0:
        arcpy.Append_management(PTPy, workcopy + "\\ChemicalTreatment_allpy", "NO_TEST", chempy)

        # Calculate State and County fields
        add_and_calculate(workcopy + "\\ChemicalTreatment_allpy", ["newx", "newy", "CNTR_PT_CN"], ["DOUBLE", "DOUBLE", "TEXT"], [0, 0, 50], ["!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], ['', '', ''])
        state_and_county("ChemicalTreatment")
        add_and_calculate("ChemicalTreatment_join", ["STATE_CD", "COUNTY_CD"], ["TEXT", "TEXT"], [2, 5], ["!STUSPS_1!", "!GEOID_1!"], ['', ''])

        # Convert UTC dates
        convert_utc_dates("ChemicalTreatment", "TRT_BEG_DT", "TRT_END_DT")
        arcpy.CopyFeatures_management("ChemicalTreatment_join2", workcopy + "\\ChemicalTreatment_join2")

        # Convert UTC times
        if 'true' in TZTM:
            arcpy.CalculateField_management("ChemicalTreatment_join2", "TRT_BEG_TM", "adddt(!TRT_BEG_TM!, !TRT_BEG_DT!)", "PYTHON3", adddt_cb)
            arcpy.CalculateField_management("ChemicalTreatment_join2", "TRT_END_TM", "adddt(!TRT_END_TM!, !TRT_END_DT!)", "PYTHON3", adddt_cb)
            arcpy.CopyFeatures_management("ChemicalTreatment_join2", "ChemicalTreatment_tz2")
            arcpy.CopyRows_management(DMgdb + "\\DST", "DST")
            arcpy.DeleteIdentical_management("ChemicalTreatment_tz2", "TIMEZONE")            
            with arcpy.da.SearchCursor("ChemicalTreatment_tz2", ["TIMEZONE", "DST"]) as cursor:
                for row in cursor:
                    tzval = str(row[0])
                    arcpy.Select_analysis("ChemicalTreatment_join2", "ChemicalTreatment_tz2_" + str(tzval) + "_NoDST", "\"TIMEZONE\" = \'" + str(tzval) + "\' AND \"DST\" = \'FALSE\'")
                    recct = arcpy.GetCount_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST").getOutput(0)
                    if int(recct) > 0:
                        arcpy.ConvertTimeZone_management("ChemicalTreatment_tz2_" + str(tzval)+ "_NoDST", "TRT_BEG_TM", "UTC", "TRT_BEG_TM_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")
                        arcpy.ConvertTimeZone_management("ChemicalTreatment_tz2_" + str(tzval)+ "_NoDST", "TRT_END_TM", "UTC", "TRT_END_TM_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")
                        arcpy.CalculateField_management("ChemicalTreatment_tz2_" + str(tzval)+ "_NoDST", "TRT_BEG_TM", "!TRT_BEG_TM_temp!", "PYTHON3")
                        arcpy.CalculateField_management("ChemicalTreatment_tz2_" + str(tzval)+ "_NoDST", "TRT_END_TM", "!TRT_END_TM_temp!", "PYTHON3")
                        arcpy.CopyFeatures_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST", "ChemicalTreatment_tz2_merge_" + str(tzval) + "_NoDST")
                    arcpy.Select_analysis("ChemicalTreatment_join2", "ChemicalTreatment_tz2_" + str(tzval) + "_DST", "\"TIMEZONE\" = \'" + str(tzval) + "\' AND \"DST\" = \'TRUE\'")
                    recct = arcpy.GetCount_management("ChemicalTreatment_tz2_" + str(tzval) + "_DST").getOutput(0)
                    if int(recct) > 0:
                        arcpy.AddField_management("ChemicalTreatment_tz2_" + str(tzval) + "_DST", "DST_FL", "TEXT", "", "", 5)
                        dst_ranges = []
                        with arcpy.da.SearchCursor("DST", ["START_DT", "END_DT"]) as dst_cur:
                            for start_dt, end_dt in dst_cur:
                                if start_dt and end_dt:
                                    dst_ranges.append((start_dt, end_dt))
                        with arcpy.da.UpdateCursor("ChemicalTreatment_tz2_" + str(tzval) + "_DST", ["TRT_BEG_TM", "DST_FL"]) as trt_cur:
                            for trt_time, dst_flag in trt_cur:
                                if not trt_time:
                                    continue
                                in_dst = any(start <= trt_time <= end for start, end in dst_ranges)
                                new_flag = 'TRUE' if in_dst else 'FALSE'
                                if dst_flag != new_flag:
                                    trt_cur.updateRow([trt_time, new_flag])
                        arcpy.Select_analysis("ChemicalTreatment_tz2_" + str(tzval) + "_DST", "ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2", "\"DST_FL\" = \'FALSE\'")
                        recct = arcpy.GetCount_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2").getOutput(0)
                        if int(recct) > 0:
                            arcpy.ConvertTimeZone_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2", "TRT_BEG_TM", "UTC", "TRT_BEG_TM_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")
                            arcpy.CalculateField_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2", "TRT_BEG_TM", "!TRT_BEG_TM_temp!", "PYTHON3")                            
                            arcpy.CopyFeatures_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2", "ChemicalTreatment_tz2_start_" + str(tzval) + "_NoDST2")
                        arcpy.Select_analysis("ChemicalTreatment_tz2_" + str(tzval) + "_DST", "ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", "\"DST_FL\" = \'TRUE\'")
                        recct = arcpy.GetCount_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST").getOutput(0)
                        if int(recct) > 0:                           
                            arcpy.ConvertTimeZone_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", "TRT_BEG_TM", "UTC", "TRT_BEG_TM_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_ADJUSTED_FOR_DST")
                            arcpy.CalculateField_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", "TRT_BEG_TM", "!TRT_BEG_TM_temp!", "PYTHON3")
                            arcpy.CopyFeatures_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", "ChemicalTreatment_tz2_start_" + str(tzval) + "_YesDST")
                        tzlist = arcpy.ListFeatureClasses("ChemicalTreatment_tz2_start_" + str(tzval) + "*")
                        tzfm = arcpy.FieldMappings()
                        tzfm = tzfm.addTable("ChemicalTreatment_join")
                        arcpy.Merge_management(tzlist, "ChemicalTreatment_starttm_" + str(tzval) + "_DST", tzfm)
                        dst_ranges = []
                        with arcpy.da.SearchCursor("DST", ["START_DT", "END_DT"]) as dst_cur:
                            for start_dt, end_dt in dst_cur:
                                if start_dt and end_dt:
                                    dst_ranges.append((start_dt, end_dt))
                        with arcpy.da.UpdateCursor("ChemicalTreatment_tz2_" + str(tzval) + "_DST", ["TRT_END_TM", "DST_FL"]) as trt_cur:
                            for trt_time, dst_flag in trt_cur:
                                if not trt_time:
                                    continue
                                in_dst = any(start <= trt_time <= end for start, end in dst_ranges)
                                new_flag = 'TRUE' if in_dst else 'FALSE'
                                if dst_flag != new_flag:
                                    trt_cur.updateRow([trt_time, new_flag])
                        arcpy.Select_analysis("ChemicalTreatment_starttm_" + str(tzval) + "_DST", "ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2", "\"DST_FL\" = \'FALSE\'")
                        recct = arcpy.GetCount_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2").getOutput(0)
                        if int(recct) > 0:
                            arcpy.ConvertTimeZone_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2", "TRT_END_TM", "UTC", "TRT_END_TM_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")                     
                            arcpy.CalculateField_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2", "TRT_END_TM", "!TRT_END_TM_temp!", "PYTHON3")                            
                            arcpy.CopyFeatures_management("ChemicalTreatment_tz2_" + str(tzval) + "_NoDST2", "ChemicalTreatment_tz2_merge_" + str(tzval) + "_NoDST2")
                        arcpy.Select_analysis("ChemicalTreatment_starttm_" + str(tzval) + "_DST", "ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", "\"DST_FL\" = \'TRUE\'")
                        recct = arcpy.GetCount_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST").getOutput(0)
                        if int(recct) > 0:
                            arcpy.ConvertTimeZone_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", "TRT_END_TM", "UTC", "TRT_END_TM_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_ADJUSTED_FOR_DST")  
                            arcpy.CalculateField_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", "TRT_END_TM", "!TRT_END_TM_temp!", "PYTHON3")
                            arcpy.CopyFeatures_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", workcopy + "\\ChemicalTreatment_tz2_" + str(tzval) + "_YesDST")
                            arcpy.CopyFeatures_management("ChemicalTreatment_tz2_" + str(tzval) + "_YesDST", "ChemicalTreatment_tz2_merge_" + str(tzval) + "_YesDST")
            tzlist = arcpy.ListFeatureClasses("ChemicalTreatment_tz2_merge_*")
            tzfm = arcpy.FieldMappings()
            tzfm = tzfm.addTable("ChemicalTreatment_join")
            arcpy.DeleteFeatures_management("ChemicalTreatment_join2")
            arcpy.Merge_management(tzlist, "ChemicalTreatment_join2", tzfm)
            
        # Calculate acreages
        calculate_treat_acres("ChemicalTreatment")

        # Calculate LGCY_FL
        arcpy.AddField_management("ChemicalTreatment_utm2", "LGCY_FL", "TEXT", "", "", 1)
        arcpy.CalculateField_management("ChemicalTreatment_utm2", "LGCY_FL", "\"" + LgcySt + "\"")

        # Calculate CMP_TY_NM
        arcpy.AddField_management("ChemicalTreatment_utm2", "CMP_TY_NM", "TEXT", "", "", 20)
        arcpy.CalculateField_management("ChemicalTreatment_utm2", "CMP_TY_NM", "\"CHEMICAL\"")

        # Append to TreatmentComponentLocation
        add_and_calculate("ChemicalTreatment_utm2", ["txBDate", "txEDate", "txBTime", "txETime"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT"], [30, 30, 30, 30], 
                          ["!TRT_BEG_DT!", "!TRT_END_DT!", "!TRT_BEG_TM!", "!TRT_END_TM!"], 
                          ['', '', '', '']) 
        arcpy.CopyFeatures_management("ChemicalTreatment_utm2", "ChemicalTreatment_fc")
        add_and_calculate("ChemicalTreatment_fc", ["perim", "apprttx_fc", "apprttx2_fc", "clcacretx", "mixvoltx_fc", "eqrttx", "temptx", "humidtx", "wndtx", "newxtx", "newytx", "adjrttx_fc", "adjactlusetx_fc", "adjrttx2_fc", "adjactlusetx2_fc"], 
                          ["TEXT"] * 15, [20] * 15, 
                          ["str(!SHAPE.LENGTH@METERS!)", "!AGT_APP_RT!", "!AGT_APP_RT2!", "!CLCACRE_ME!", "!MIXVOL_ME!", "!EQ_OUT_RT!", "!FA_AIR_ME!", "!HUMID_RT!", "!WNDMPH_ME!", "!newx!", "!newy!", "!ADJ_AGT_APP_RT!", "!ADJ_ACTLUSE_QTY!", "!ADJ_AGT_APP_RT2!", "!ADJ_ACTLUSE_QTY2!"], 
                          [''] * 15) 
        row_pairs = set()
        with arcpy.da.UpdateCursor("ChemicalTreatment_fc", ["AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "txBDate", "txEDate", "txBTime", "txETime", "PHNLGY_NM", "DPC_TX", "MIXUOM_NM", "mixvoltx_fc", "CARR_TY_NM", "RLSDRCT_TX", "PUP_NR", "DLVR_NM", "PTTRN_NM", "WTRDIST_TX", "eqrttx", "EQ_UOM_NM", "EQ_TY_NM", "temptx", "humidtx", "wndtx", "SL_MOIS_NM", "PRECIP_NM", "WNDDRCT_CD", "newx", "newy", "perim", "clcacretx", "TRADE_NM", "APP_UOM_NM", "TRADE_NM2", "APP_UOM_NM2", "ADJ_TRADE_NM", "ADJ_TRADE_NM2", "apprttx_fc", "apprttx2_fc", "adjrttx_fc", "adjactlusetx_fc", "ADJ_APP_UOM_NM", "adjrttx2_fc", "adjactlusetx2_fc", "ADJ_APP_UOM_NM2", "NOTES"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyFeatures_management("ChemicalTreatment_fc", workcopy + "\\chem_ident_removed")
        arcpy.AddField_management("ChemicalTreatment_fc", "TRT_GUID", "GUID")
        arcpy.CalculateField_management("ChemicalTreatment_fc", "TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        arcpy.AddField_management("ChemicalTreatment_fc", "CONAGT_GUID", "GUID")
        arcpy.CalculateField_management("ChemicalTreatment_fc", "CONAGT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        chemfm = arcpy.FieldMappings()
        chemfm.addTable(Outgdb + "\\TreatmentComponentLocation")
        arcpy.Append_management("ChemicalTreatment_fc", Outgdb + "\\TreatmentComponentLocation", "NO_TEST", chemfm)

        # Merge to CHEMICALCOMPONENT
        add_and_calculate("ChemicalTreatment_utm2", ["cvrrttx", "apprttx", "apprttx2", "actusetx", "actusetx2", "mixvoltx", "clcacretx"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [20, 20, 20, 20, 20, 20, 20], 
                          ["!EST_CVR_RT!", "!AGT_APP_RT!", "!AGT_APP_RT2!", "!ACTLUSE_QY!", "!ACTLUSE_QY2!", "!MIXVOL_ME!", "!CLCACRE_ME!"], 
                          ['', '', '', '', '', '', '']) 
        add_and_calculate("ChemicalTreatment_fc", ["actusetx_fc", "actusetx2_fc", "DLVR_NM_fc", "PTTRN_NM_fc", "TRADE_NM_fc", "txBDate_fc", "txEDate_fc", "CARR_TY_NM_fc", "TRADE_NM2_fc", "PHNLGY_NM_fc", "RECORDER_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [20, 20, 10, 10, 40, 30, 30, 30, 40, 20, 50], 
                          ["!ACTLUSE_QY!", "!ACTLUSE_QY2!", "!DLVR_NM!", "!PTTRN_NM!", "!TRADE_NM!", "!txBDate!", "!txEDate!", "!CARR_TY_NM!", "!TRADE_NM2!", "!PHNLGY_NM!", "!RECORDER!"], 
                          ['', '', '', '', '', '', '', '', '', '', ''])
        update_chem_time(["ChemicalTreatment_utm2", "ChemicalTreatment_fc"])
        add_and_calculate("ChemicalTreatment_fc", ["txBTime_fc", "TRT_END_DT_fc", "WTRDIST_TX_fc", "LOC_NM_fc", "clcacretx_fc", "joinid_fc", "NOTES_fc"], 
                          ["TEXT", "DATE", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 0, 30, 100, 20, 10, 255], 
                          ["!txBTime!", "!TRT_END_DT!", "!WTRDIST_TX!", "!LOC_NM!", "!clcacretx!", "!joinid!", "!NOTES!"], 
                          ['', '', '', '', '', '', '']) 
        arcpy.AddField_management("ChemicalTreatment_utm2", "joinid_tx", "TEXT", "", "", 10)
        arcpy.CalculateField_management("ChemicalTreatment_utm2", "joinid_tx", "!joinid!", "PYTHON3")
        arcpy.DeleteField_management("ChemicalTreatment_fc", "clcacretx;LOC_NM;RECORDER;WTRDIST_TX;DLVR_NM;PTTRN_NM;TRT_BEG_DT;CARR_TY_NM;TRADE_NM2;MIXVOL_ME;ADJ_AGT_APP_RT;ADJ_ACTLUSE_QTY;PHNLGY_NM;txBDate;txBTime")
        chmtbfm = arcpy.FieldMappings()
        chmtbfm.addTable("ChemicalTreatment_utm2")
        chmtbfm.addTable("ChemicalTreatment_fc")        
        arcpy.SpatialJoin_analysis("ChemicalTreatment_utm2", "ChemicalTreatment_fc", "ChemicalTreatmentData_chem", "JOIN_ONE_TO_MANY", "KEEP_COMMON", chmtbfm, "ARE_IDENTICAL_TO", "", "")
        with arcpy.da.UpdateCursor("ChemicalTreatmentData_chem", "*", "\"clcacretx\" <> \"clcacretx_fc\" OR \"LOC_NM\" <> \"LOC_NM_fc\" OR \"WTRDIST_TX\" <> \"WTRDIST_TX_fc\" OR \"DLVR_NM\" <> \"DLVR_NM_fc\" OR \"PTTRN_NM\" <> \"PTTRN_NM_fc\" OR \"TRADE_NM\" <> \"TRADE_NM_fc\" OR \"txBDate\" <> \"txBDate_fc\" OR \"txEDate\" <> \"txEDate_fc\" OR \"CARR_TY_NM\" <> \"CARR_TY_NM_fc\" OR \"TRADE_NM2\" <> \"TRADE_NM2_fc\" OR (\"TRADE_NM2\" IS NOT NULL AND \"TRADE_NM2_fc\" IS NULL) OR (\"TRADE_NM2\" IS NULL AND \"TRADE_NM2_fc\" IS NOT NULL) OR \"apprttx\" <> \"apprttx_fc\" OR (\"apprttx\" IS NOT NULL AND \"apprttx_fc\" IS NULL) OR (\"apprttx\" IS NULL AND \"apprttx_fc\" IS NOT NULL) OR \"actusetx\" <> \"actusetx_fc\" OR (\"actusetx\" IS NOT NULL AND \"actusetx_fc\" IS NULL) OR (\"actusetx\" IS NULL AND \"actusetx_fc\" IS NOT NULL) OR \"apprttx2\" <> \"apprttx2_fc\" OR (\"apprttx2\" IS NOT NULL AND \"apprttx2_fc\" IS NULL) OR (\"apprttx2\" IS NULL AND \"apprttx2_fc\" IS NOT NULL) OR \"actusetx2\" <> \"actusetx2_fc\" OR (\"actusetx2\" IS NOT NULL AND \"actusetx2_fc\" IS NULL) OR (\"actusetx2\" IS NULL AND \"actusetx2_fc\" IS NOT NULL) OR \"mixvoltx\" <> \"mixvoltx_fc\" OR \"PHNLGY_NM\" <> \"PHNLGY_NM_fc\" OR (\"PHNLGY_NM\" IS NOT NULL AND \"PHNLGY_NM_fc\" IS NULL) OR (\"PHNLGY_NM\" IS NULL AND \"PHNLGY_NM_fc\" IS NOT NULL)OR \"RECORDER\" <> \"RECORDER_fc\" OR \"txBTime\" <> \"txBTime_fc\" OR (\"txBTime\" IS NOT NULL AND \"txBTime_fc\" IS NULL) OR (\"txBTime\" IS NULL AND \"txBTime_fc\" IS NOT NULL) OR \"NOTES\" <> \"NOTES_fc\"") as cursor:
            for row in cursor:
                cursor.deleteRow()
        arcpy.CopyFeatures_management("ChemicalTreatmentData_chem", "ChemicalTreatmentData_chemcomp")
        row_pairs = set()
        with arcpy.da.UpdateCursor("ChemicalTreatmentData_chemcomp", ["TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management("ChemicalTreatmentData_chemcomp", "chemtb_all")
        chemcompfm = arcpy.FieldMappings()
        chemcompfm.addTable(Outgdb + "\\CHEMICALCOMPONENT")
        arcpy.Append_management("chemtb_all", Outgdb + "\\CHEMICALCOMPONENT", "NO_TEST", chemcompfm)

        # Split out SCNTFC_CD fields
        arcpy.DeleteField_management("ChemicalTreatmentData_chem", "SCNTFC_CD_1")
        arcpy.CopyFeatures_management("ChemicalTreatmentData_chem", "ChemicalTreatmentData_spp")
        treat_species_append("ChemicalTreatmentData")

        #Calculate net acreage for CHEMICALCOMPONENT table
        arcpy.JoinField_management(Outgdb + "\\CHEMICALCOMPONENT", "TRT_GUID", "ChemicalTreatmentData_cvrsum", "TRT_GUID", ["SUM_EST_CVR_RT", "CLCACRE_ME"])
        arcpy.CalculateField_management(Outgdb + "\\CHEMICALCOMPONENT", "ESTACRE_ME", "accalc(!ESTACRE_ME!, !SUM_EST_CVR_RT!,!CLCACRE_ME!)", "PYTHON3", trtac_cb)
        arcpy.JoinField_management("ChemicalTreatmentData_cvrsum", "TRT_GUID", Outgdb + "\\CHEMICALCOMPONENT", "TRT_GUID", ["ESTACRE_ME", "PTTRN_NM"])
        arcpy.DeleteField_management(Outgdb + "\\CHEMICALCOMPONENT", "SUM_EST_CVR_RT;CLCACRE_ME")
            
        # Split out TRADE_NM fields
        arcpy.DeleteField_management("ChemicalTreatmentData_chem", "TRADE_NM_fc")
        arcpy.DeleteField_management("ChemicalTreatmentData_chem", "TRADE_NM2_fc")
        arcpy.CreateFeatureclass_management("memory", "ChemicalTreatmentData_herb", "POLYGON", "ChemicalTreatmentData_chem", "", "", new_spatialref)
        HerbNum = 1
        for field in arcpy.ListFields("ChemicalTreatmentData_chem", "TRADE_NM*"):
            arcpy.Select_analysis("ChemicalTreatmentData_chem", "chemtb5_" + str(HerbNum), "\"" + field.name + "\"" + " IS NOT NULL")
            RecNum = arcpy.GetCount_management("chemtb5_" + str(HerbNum)).getOutput(0)
            if int(RecNum) > 0:
                arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "TRADE_NM", "!" + field.name + "!", "PYTHON3")
                ChemNum = str(field.name)
                ChemNum = ChemNum.strip("TRADE_NM")
                ChemAgRt = str("AGT_APP_RT" + ChemNum)
                arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "AGT_APP_RT", "!" + ChemAgRt + "!", "PYTHON3")
                ChemApU = str("APP_UOM_NM" + ChemNum)
                arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "APP_UOM_NM", "!" + ChemApU + "!", "PYTHON3")
                ChemQty = str("ACTLUSE_QY" + ChemNum)
                arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "ACTLUSE_QY", "!" + ChemQty + "!", "PYTHON3")
                ChemAgU = str("AGT_UOM_NM" + ChemNum)
                arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "AGT_UOM_NM", "!" + ChemAgU + "!", "PYTHON3")                    
                ChemMfr = str("MNFCTR_NM" + ChemNum)
                arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "MNFCTR_NM", "!" + ChemMfr + "!", "PYTHON3")
                ChemEPA = str("EPAREGISTRATIONNUMBER" + ChemNum)
                arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "EPAREGISTRATIONNUMBER", "!" + ChemEPA + "!", "PYTHON3")
                HerbNum += 1
        herbfld = arcpy.ListFeatureClasses("chemtb5_*")
        arcpy.Append_management(herbfld, "ChemicalTreatmentData_herb")
        arcpy.Select_analysis("ChemicalTreatmentData_herb", "ChemicalTreatmentData_herbsel", "\"TRADE_NM\" IS NOT NULL")
        herbcnt = arcpy.GetCount_management("ChemicalTreatmentData_herbsel").getOutput(0)
        if int(herbcnt) > 0:
            row_pairs = set()
            with arcpy.da.UpdateCursor("ChemicalTreatmentData_herbsel", ["TRADE_NM", "TRT_GUID"]) as cursor:
                for row in cursor:
                    row_pair = tuple(row)
                    if row_pair in row_pairs:
                        cursor.deleteRow()
                    else:
                        row_pairs.add(row_pair)
                        
            # Calculate AGT_UOM_NM and ACTLUSE_QY and merge to CHEMICALCOMPCONTROLAGENT
            arcpy.JoinField_management("ChemicalTreatmentData_herbsel", "TRT_GUID", "ChemicalTreatmentData_cvrsum", "TRT_GUID", ["ESTACRE_ME", "PTTRN_NM"])                     
            arcpy.CalculateField_management("ChemicalTreatmentData_herbsel", "ACTLUSE_QY", "Calc(!AGT_APP_RT!, !APP_UOM_NM!, !ACTLUSE_QY!, !ESTACRE_ME!, !MIXVOL_ME!, !PTTRN_NM!, !CLCACRE_ME!)", "PYTHON3", act_cb)
            arcpy.CalculateField_management("ChemicalTreatmentData_herbsel", "AGT_UOM_NM", "Calc(!AGT_UOM_NM!, !APP_UOM_NM!, !MIXUOM_NM!)", "PYTHON3", agt_cb)
            arcpy.CalculateField_management("ChemicalTreatmentData_herbsel", "AGT_APP_RT", "Calc(!AGT_APP_RT!, !ACTLUSE_QY!, !PTTRN_NM!, !CLCACRE_ME!, !ESTACRE_ME!)", "PYTHON3", rt_cb)
            arcpy.CalculateField_management("ChemicalTreatmentData_herbsel", "APP_UOM_NM", "Calc(!APP_UOM_NM!, !AGT_UOM_NM!)", "PYTHON3", rtuom_cb) 
            arcpy.CopyRows_management("ChemicalTreatmentData_herbsel", "chemtb_all")
            chemagfm = arcpy.FieldMappings()
            chemagfm.addTable(Outgdb + "\\CHEMICALCOMPCONTROLAGENT")
            arcpy.Append_management("chemtb_all", Outgdb + "\\CHEMICALCOMPCONTROLAGENT", "NO_TEST", chemagfm)

        # Split out ADJ_TRADE_NM
        arcpy.DeleteField_management("ChemicalTreatmentData_chem", "ADJ_TRADE_NM_fc")
        arcpy.DeleteField_management("ChemicalTreatmentData_chem", "ADJ_TRADE_NM2_fc")
        arcpy.AddField_management("ChemicalTreatmentData_chem", "ACTLUSE_QTY", "DOUBLE")
        arcpy.AddField_management("ChemicalTreatmentData_chem", "AGT_UOM_NM", "TEXT", "", "", 30)
        arcpy.CreateFeatureclass_management("memory", "ChemicalTreatmentData_adj", "POLYGON", "ChemicalTreatmentData_chem", "", "", new_spatialref)
        AdjNum = 1
        for field in arcpy.ListFields("ChemicalTreatmentData_chem", "ADJ_TRADE_NM*"): 
            arcpy.Select_analysis("ChemicalTreatmentData_chem", "chemtb7_" + str(AdjNum), "\"" + field.name + "\"" + " IS NOT NULL AND \"" + field.name + "\" <> \'\'")
            RecNum = arcpy.GetCount_management("chemtb7_" + str(AdjNum)).getOutput(0)
            if int(RecNum) > 0:
                AdjNR = str(field.name)
                AdjNR = AdjNR.strip("ADJ_TRADE_NM")
                arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "TRADE_NM", "!" + field.name + "!", "PYTHON3")
                AdjUnit = str("ADJ_AGT_UOM_NM" + AdjNR) 
                arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "AGT_UOM_NM", "!" + AdjUnit + "!", "PYTHON3")
                AdjAgRt = str("ADJ_AGT_APP_RT" + AdjNR)
                arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "AGT_APP_RT", "!" + AdjAgRt + "!", "PYTHON3")
                AdjApU = str("ADJ_APP_UOM_NM" + AdjNR)
                arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "APP_UOM_NM", "!" + AdjApU + "!", "PYTHON3")
                AdjAct = str("ADJ_ACTLUSE_QTY" + AdjNR)
                arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "ACTLUSE_QTY", "!" + AdjAct + "!", "PYTHON3")
                AdjNum += 1
        adjfld = arcpy.ListFeatureClasses("chemtb7_*")
        arcpy.Append_management(adjfld, "ChemicalTreatmentData_adj", "NO_TEST")
        arcpy.Select_analysis("ChemicalTreatmentData_adj", "ChemicalTreatmentData_adjsel", "\"TRADE_NM\" IS NOT NULL")
        adjcnt = arcpy.GetCount_management("ChemicalTreatmentData_adjsel").getOutput(0)
        if int(adjcnt) > 0:                                
            row_pairs = set()
            with arcpy.da.UpdateCursor("ChemicalTreatmentData_adjsel", ["TRT_GUID", "CONAGT_GUID", "AGT_UOM_NM", "ACTLUSE_QTY", "TRADE_NM", "AGT_APP_RT", "APP_UOM_NM"]) as cursor:
                for row in cursor:
                    row_pair = tuple(row)
                    if row_pair in row_pairs:
                        cursor.deleteRow()
                    else:
                        row_pairs.add(row_pair)
            arcpy.CopyRows_management("ChemicalTreatmentData_adjsel", "chemtb_all", "NO_TEST")
            chemadjfm = arcpy.FieldMappings()
            chemadjfm.addTable(Outgdb + "\\ADJUVANTCOMPONENTAGENT")
            arcpy.Append_management("chemtb_all", Outgdb + "\\ADJUVANTCOMPONENTAGENT", "NO_TEST", chemadjfm)
                
    # Set TreatmentComponentData as workspace
    arcpy.env.workspace = workcopy + "\\TreatmentData"

    # Check for data in each Fire feature class
    arcpy.AddMessage("Processing fire treatment data.")
    project_albers_treat("Fire")    

    # Buffer line and point data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("Fire")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "FireTreatment_allpy", "POLYGON", workcopy + "\\TreatmentData\\FireComponentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("Fire*Py_gcs")
    PTPyCt = len(PTPy)
    firepy = arcpy.FieldMappings()
    firepy.addTable(workcopy + "\\TreatmentData\\FireComponentPy")    
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\FireTreatment_allpy", "NO_TEST", firepy)

        # Calculate State and County fields
        add_and_calculate(workcopy + "\\FireTreatment_allpy", ["newx", "newy", "CNTR_PT_CN"], ["DOUBLE", "DOUBLE", "TEXT"], [0, 0, 50], ["!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], ['', '', ''])
        state_and_county("FireTreatment")
        add_and_calculate("FireTreatment_join", ["STATE_CD", "COUNTY_CD"], ["TEXT", "TEXT"], [2, 5], ["!STUSPS_1!", "!GEOID_1!"], ['', ''])

        # Convert UTC dates
        convert_utc_dates("FireTreatment", "TRT_BEG_DT", "TRT_END_DT")

        # Calculate acreages
        calculate_treat_acres("FireTreatment")

        # Calculate LGCY_FL        
        arcpy.AddField_management("FireTreatment_utm2", "LGCY_FL", "TEXT", "", "", 1)
        arcpy.CalculateField_management("FireTreatment_utm2", "LGCY_FL", "\"" + LgcySt + "\"")

        # Calculate CMP_TY_NM
        arcpy.AddField_management("FireTreatment_utm2", "CMP_TY_NM", "TEXT", "", "", 20)
        arcpy.CalculateField_management("FireTreatment_utm2", "CMP_TY_NM", "\"FIRE\"")
    
        # Append to TreatmentComponentLocation
        add_and_calculate("FireTreatment_utm2", ["rejoin_ct", "txBDate", "txEDate"], 
                          ["LONG", "TEXT", "TEXT"], [0, 30, 30], 
                          ["autoIncrement()", "!TRT_BEG_DT!", "!TRT_END_DT!"], 
                          [count_cb, '', '']) 
        arcpy.CopyFeatures_management("FireTreatment_utm2", "FireTreatment_fc")
        add_and_calculate("FireTreatment_fc", ["perim", "newxtx", "newytx", "clcacretx_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT"], [20, 20, 20, 20], 
                          ["str(!SHAPE.LENGTH@METERS!)", "!newx!", "!newy!", "!CLCACRE_ME!"], 
                          ['', '', '', '']) 
        row_pairs = set()
        with arcpy.da.UpdateCursor("FireTreatment_fc", ["AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "txBDate", "txEDate", "PHNLGY_NM", "DPC_TX", "INTNSTY_NM", "FUELMDL_TX", "newx", "newy", "perim", "clcacretx_fc", "NOTES"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("FireTreatment_fc", "TRT_GUID", "GUID")
        arcpy.CalculateField_management("FireTreatment_fc", "TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        firefm = arcpy.FieldMappings()
        firefm.addTable(Outgdb + "\\TreatmentComponentLocation")
        arcpy.Append_management("FireTreatment_fc", Outgdb + "\\TreatmentComponentLocation", "NO_TEST", firefm)

        # Merge to FIRECOMPONENT
        add_and_calculate("FireTreatment_fc", ["INTNSTY_NM_fc", "FUELMDL_TX_fc", "txBDate_fc", "clcacretx"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT"], [30, 40, 30, 20], 
                          ["!INTNSTY_NM!", "!FUELMDL_TX!", "!TRT_BEG_DT!", "!CLCACRE_ME!"], 
                          ['', '', '', '']) 
        firtbfm = arcpy.FieldMappings()
        firtbfm.addTable("FireTreatment_utm2")
        firtbfm.addTable("FireTreatment_fc")
        arcpy.SpatialJoin_analysis("FireTreatment_utm2", "FireTreatment_fc", "FireTreatmentData_fire", "JOIN_ONE_TO_MANY", "KEEP_COMMON", firtbfm, "ARE_IDENTICAL_TO", "", "")
        arcpy.Select_analysis("FireTreatmentData_fire", "FireTreatmentData_spp", "\"INTNSTY_NM\" = \"INTNSTY_NM_fc\" AND \"FUELMDL_TX\" = \"FUELMDL_TX_fc\" AND \"txBDate\" = \"txBDate_fc\" AND \"clcacretx\" = \"clcacretx_fc\"")
        arcpy.Select_analysis("FireTreatmentData_fire", "FireTreatmentData_firetb2", "\"INTNSTY_NM\" IS NULL OR \"FUELMDL_TX\" IS NULL")
        arcpy.Append_management("FireTreatmentData_firetb2", "FireTreatmentData_spp", "NO_TEST", firtbfm)
        row_pairs = set()
        with arcpy.da.UpdateCursor("FireTreatmentData_spp", ["INTNSTY_NM", "FUELMDL_TX", "TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management("FireTreatmentData_spp", "firetb2")
        firecompfm = arcpy.FieldMappings()
        firecompfm.addTable(Outgdb + "\\FIRECOMPONENT")
        arcpy.Append_management("firetb2", Outgdb + "\\FIRECOMPONENT", "NO_TEST", firecompfm)

        # Split out SCNTFC_CD fields
        arcpy.DeleteField_management("FireTreatmentData_spp", "SCNTFC_CD_1")
        treat_species_append("FireTreatmentData")

    # Set TreatmentData as workspace
    arcpy.env.workspace = workcopy + "\\TreatmentData"

    # Check for data in each Manual feature class
    arcpy.AddMessage("Processing manual treatment data.")
    project_albers_treat("Manual")

    # Buffer line and point data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("Manual")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "ManualTreatment_allpy", "POLYGON", workcopy + "\\TreatmentData\\ManualComponentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("Manual*Py_gcs")
    PTPyCt = len(PTPy)
    manpy = arcpy.FieldMappings()
    manpy.addTable(workcopy + "\\TreatmentData\\ManualComponentPy")    
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\ManualTreatment_allpy", "NO_TEST", manpy)

        # Calculate State and County fields
        add_and_calculate(workcopy + "\\ManualTreatment_allpy", ["newx", "newy", "CNTR_PT_CN"], ["DOUBLE", "DOUBLE", "TEXT"], [0, 0, 50], ["!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], ['', '', ''])
        state_and_county("ManualTreatment")
        add_and_calculate("ManualTreatment_join", ["STATE_CD", "COUNTY_CD"], ["TEXT", "TEXT"], [2, 5], ["!STUSPS_1!", "!GEOID_1!"], ['', ''])

        # Convert UTC dates
        convert_utc_dates("ManualTreatment", "TRT_BEG_DT", "TRT_END_DT")
        
        # Calculate acreages
        calculate_treat_acres("ManualTreatment")

        # Calculate LGCY_FL
        arcpy.AddField_management("ManualTreatment_utm2", "LGCY_FL", "TEXT", "", "", 1)
        arcpy.CalculateField_management("ManualTreatment_utm2", "LGCY_FL", "\"" + LgcySt + "\"")

        # Calculate CMP_TY_NM
        arcpy.AddField_management("ManualTreatment_utm2", "CMP_TY_NM", "TEXT", "", "", 20)
        arcpy.CalculateField_management("ManualTreatment_utm2", "CMP_TY_NM", "\"MANUAL\"")

        # Append to TreatmentComponentLocation
        add_and_calculate("ManualTreatment_utm2", ["txBDate", "txEDate", "clcacretx"], ["TEXT", "TEXT", "TEXT"], [30, 30, 20], ["!TRT_BEG_DT!", "!TRT_END_DT!", "!CLCACRE_ME!"], ['', '', ''])
        arcpy.CopyFeatures_management("ManualTreatment_utm2", "ManualTreatment_fc")
        add_and_calculate("ManualTreatment_fc", ["perim", "newxtx", "newytx", "clcacretx_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT"], [20, 20, 20, 20], 
                          ["str(!SHAPE.LENGTH@METERS!)", "!newx!", "!newy!", "!CLCACRE_ME!"], 
                          ['', '', '', ''])
        row_pairs = set()
        with arcpy.da.UpdateCursor("ManualTreatment_fc", ["AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "txBDate", "txEDate", "PHNLGY_NM", "DPC_TX", "MANL_CL_NM", "newx", "newy", "perim", "clcacretx_fc", "NOTES"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("ManualTreatment_fc", "TRT_GUID", "GUID")
        arcpy.CalculateField_management("ManualTreatment_fc", "TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        manfm = arcpy.FieldMappings()
        manfm.addTable(Outgdb + "\\TreatmentComponentLocation")
        arcpy.Append_management("ManualTreatment_fc", Outgdb + "\\TreatmentComponentLocation", "NO_TEST", manfm)

        # Merge to MANUALCOMPONENT
        add_and_calculate("ManualTreatment_fc", ["MANL_CL_NM_fc", "txBDate_fc", "PHNLGY_NM_fc", "LOC_NM_fc", "RECORDER_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 30, 20, 100, 50], 
                          ["!MANL_CL_NM!", "!txBDate!", "!PHNLGY_NM!", "!LOC_NM!", "!RECORDER!"], 
                          ['', '', '', '', ''])
        mantbfm = arcpy.FieldMappings()
        mantbfm.addTable("ManualTreatment_utm2")
        mantbfm.addTable("ManualTreatment_fc")        
        arcpy.SpatialJoin_analysis("ManualTreatment_utm2", "ManualTreatment_fc", "ManualTreatmentData_spp", "JOIN_ONE_TO_MANY", "KEEP_COMMON", mantbfm, "ARE_IDENTICAL_TO", "", "")
        with arcpy.da.UpdateCursor("ManualTreatmentData_spp", "*", "\"MANL_CL_NM\" <> \"MANL_CL_NM_fc\" OR \"txBDate\" <> \"txBDate_fc\" OR \"PHNLGY_NM\" <> \"PHNLGY_NM_fc\" OR \"LOC_NM\" <> \"LOC_NM_fc\" OR \"RECORDER\" <> \"RECORDER_fc\" OR \"clcacretx\" <> \"clcacretx_fc\"") as cursor:
            for row in cursor:
                cursor.deleteRow()
        row_pairs = set()
        arcpy.CopyFeatures_management("ManualTreatmentData_spp", "ManualTreatmentData_mantb")
        with arcpy.da.UpdateCursor("ManualTreatmentData_mantb", ["MANL_CL_NM", "TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management("ManualTreatmentData_mantb", "mantb2")
        mancompfm = arcpy.FieldMappings()
        mancompfm.addTable(Outgdb + "\\MANUALCOMPONENT")
        arcpy.Append_management("mantb2", Outgdb + "\\MANUALCOMPONENT", "NO_TEST", mancompfm)

        # Split out SCNTFC_CD fields
        treat_species_append("ManualTreatmentData")

        # Calculate net acreage for MANUALCOMPONENT table
        arcpy.JoinField_management(Outgdb + "\\MANUALCOMPONENT", "TRT_GUID", "ManualTreatmentData_cvrsum", "TRT_GUID", ["SUM_EST_CVR_RT", "CLCACRE_ME"])
        arcpy.CalculateField_management(Outgdb + "\\MANUALCOMPONENT", "MANLCMP_ME", "accalc(!MANLCMP_ME!, !SUM_EST_CVR_RT!,!CLCACRE_ME!)", "PYTHON3", trtac_cb)
        arcpy.DeleteField_management(Outgdb + "\\MANUALCOMPONENT", "SUM_EST_CVR_RT;CLCACRE_ME")

    # Set TreatmentData as workspace
    arcpy.env.workspace = workcopy + "\\TreatmentData"

    # Check for data in each Mechanical feature class
    arcpy.AddMessage("Processing mechanical treatment data.")
    project_albers_treat("Mechanical")

    # Buffer line and point data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("Mechanical")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "MechanicalTreatment_allpy", "POLYGON", workcopy + "\\TreatmentData\\MechanicalComponentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("Mechanical*Py_gcs")
    PTPyCt = len(PTPy)
    mechpy = arcpy.FieldMappings()
    mechpy.addTable(workcopy + "\\TreatmentData\\MechanicalComponentPy")    
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\MechanicalTreatment_allpy", "NO_TEST", mechpy)

        # Calculate State and County fields
        add_and_calculate(workcopy + "\\MechanicalTreatment_allpy", ["newx", "newy", "CNTR_PT_CN"], ["DOUBLE", "DOUBLE", "TEXT"], [0, 0, 50], ["!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], ['', '', ''])
        state_and_county("MechanicalTreatment")
        add_and_calculate("MechanicalTreatment_join", ["STATE_CD", "COUNTY_CD"], ["TEXT", "TEXT"], [2, 5], ["!STUSPS_1!", "!GEOID_1!"], ['', ''])

        # Convert UTC dates
        convert_utc_dates("MechanicalTreatment", "TRT_BEG_DT", "TRT_END_DT")            

        # Calculate acreages
        calculate_treat_acres("MechanicalTreatment")
        
        # Calculate LGCY_FL
        arcpy.AddField_management("MechanicalTreatment_utm2", "LGCY_FL", "TEXT", "", "", 1)
        arcpy.CalculateField_management("MechanicalTreatment_utm2", "LGCY_FL", "\"" + LgcySt + "\"")

        # Calculate CMP_TY_NM
        arcpy.AddField_management("MechanicalTreatment_utm2", "CMP_TY_NM", "TEXT", "", "", 20)
        arcpy.CalculateField_management("MechanicalTreatment_utm2", "CMP_TY_NM", "\"MECHANICAL\"")

        # Append to TreatmentComponentLocation
        add_and_calculate("MechanicalTreatment_utm2", ["txBDate", "txEDate", "clcacretx"], ["TEXT", "TEXT", "TEXT"], [30, 30, 20], ["!TRT_BEG_DT!", "!TRT_END_DT!", "!CLCACRE_ME!"], ['', '', ''])
        arcpy.CopyFeatures_management("MechanicalTreatment_utm2", "MechanicalTreatment_fc")
        add_and_calculate("MechanicalTreatment_fc", ["perim", "newxtx", "newytx", "clcacretx_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT"], [20, 20, 20, 20], 
                          ["str(!SHAPE.LENGTH@METERS!)", "!newx!", "!newy!", "!CLCACRE_ME!"], 
                          ['', '', '', ''])
        row_pairs = set()
        with arcpy.da.UpdateCursor("MechanicalTreatment_fc", ["AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "txBDate", "txEDate", "PHNLGY_NM", "DPC_TX", "MECH_CL_NM", "newx", "newy", "perim", "clcacretx_fc", "NOTES"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("MechanicalTreatment_fc", "TRT_GUID", "GUID")
        arcpy.CalculateField_management("MechanicalTreatment_fc", "TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        mechfm = arcpy.FieldMappings()
        mechfm.addTable(Outgdb + "\\TreatmentComponentLocation")
        arcpy.Append_management("MechanicalTreatment_fc", Outgdb + "\\TreatmentComponentLocation", "NO_TEST", mechfm)
                                
        # Merge to MECHANICALCOMPONENT
        add_and_calculate("MechanicalTreatment_fc", ["MECH_CL_NM_fc", "txBDate_fc", "PHNLGY_NM_fc", "LOC_NM_fc", "RECORDER_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 30, 20, 100, 50], 
                          ["!MECH_CL_NM!", "!txBDate!", "!PHNLGY_NM!", "!LOC_NM!", "!RECORDER!"], 
                          ['', '', '', '', ''])
        mchtbfm = arcpy.FieldMappings()
        mchtbfm.addTable("MechanicalTreatment_utm2")
        mchtbfm.addTable("MechanicalTreatment_fc")        
        arcpy.SpatialJoin_analysis("MechanicalTreatment_utm2", "MechanicalTreatment_fc", "MechanicalTreatmentData_spp", "JOIN_ONE_TO_MANY", "KEEP_COMMON", mchtbfm, "ARE_IDENTICAL_TO", "", "")
        with arcpy.da.UpdateCursor("MechanicalTreatmentData_spp", "*", "\"MECH_CL_NM\" <> \"MECH_CL_NM_fc\" OR \"txBDate\" <> \"txBDate_fc\" OR \"PHNLGY_NM\" <> \"PHNLGY_NM_fc\" OR \"LOC_NM\" <> \"LOC_NM_fc\" OR \"RECORDER\" <> \"RECORDER_fc\" OR \"clcacretx\" <> \"clcacretx_fc\"") as cursor:
            for row in cursor:
                cursor.deleteRow()
        row_pairs = set()
        arcpy.CopyFeatures_management("MechanicalTreatmentData_spp", "MechanicalTreatmentData_mchtb")
        with arcpy.da.UpdateCursor("MechanicalTreatmentData_mchtb", ["MECH_CL_NM", "TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management("MechanicalTreatmentData_mchtb", "mchtb2")
        mchcompfm = arcpy.FieldMappings()
        mchcompfm.addTable(Outgdb + "\\MECHANICALCOMPONENT")
        arcpy.Append_management("mchtb2", Outgdb + "\\MECHANICALCOMPONENT", "NO_TEST", mchcompfm)

        # Split out SCNTFC_CD fields
        treat_species_append("MechanicalTreatmentData")

        # Calculate net acreage for MECHANICALCOMPONENT table
        arcpy.JoinField_management(Outgdb + "\\MECHANICALCOMPONENT", "TRT_GUID", "MechanicalTreatmentData_cvrsum", "TRT_GUID", ["SUM_EST_CVR_RT", "CLCACRE_ME"])
        arcpy.CalculateField_management(Outgdb + "\\MECHANICALCOMPONENT", "MECHCMP_ME", "accalc(!MECHCMP_ME!, !SUM_EST_CVR_RT!,!CLCACRE_ME!)", "PYTHON3", trtac_cb)
        arcpy.DeleteField_management(Outgdb + "\\MECHANICALCOMPONENT", "SUM_EST_CVR_RT;CLCACRE_ME")

    # Set TreatmentData as workspace
    arcpy.env.workspace = workcopy + "\\TreatmentData"

    # Check for data in each Manual feature class
    arcpy.AddMessage("Processing restoration data.")
    project_albers_treat("Restoration")

    # Buffer line and point data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("Restoration")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "RestorationTreatment_allpy", "POLYGON", workcopy + "\\TreatmentData\\RestorationComponentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("Restoration*Py_gcs")
    PTPyCt = len(PTPy)
    respy = arcpy.FieldMappings()
    respy.addTable(workcopy + "\\TreatmentData\\RestorationComponentPy")    
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\RestorationTreatment_allpy", "NO_TEST", respy)

        # Calculate State and County fields
        add_and_calculate(workcopy + "\\RestorationTreatment_allpy", ["newx", "newy", "CNTR_PT_CN"], ["DOUBLE", "DOUBLE", "TEXT"], [0, 0, 50], ["!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], ['', '', ''])
        state_and_county("RestorationTreatment")
        add_and_calculate("RestorationTreatment_join", ["STATE_CD", "COUNTY_CD"], ["TEXT", "TEXT"], [2, 5], ["!STUSPS_1!", "!GEOID_1!"], ['', ''])

        # Convert UTC dates
        convert_utc_dates("RestorationTreatment", "TRT_BEG_DT", "TRT_END_DT")
        
        # Calculate acreages
        calculate_treat_acres("RestorationTreatment")

        # Calculate LGCY_FL
        arcpy.AddField_management("RestorationTreatment_utm2", "LGCY_FL", "TEXT", "", "", 1)
        arcpy.CalculateField_management("RestorationTreatment_utm2", "LGCY_FL", "\"" + LgcySt + "\"")

        # Calculate CMP_TY_NM
        arcpy.AddField_management("RestorationTreatment_utm2", "CMP_TY_NM", "TEXT", "", "", 20)
        arcpy.CalculateField_management("RestorationTreatment_utm2", "CMP_TY_NM", "\"RESTORATION\"")

        # Append to TreatmentComponentLocation
        add_and_calculate("RestorationTreatment_utm2", ["txBDate", "txEDate", "clcacretx"], 
                          ["TEXT", "TEXT", "TEXT"], [30, 30, 20], 
                          ["!TRT_BEG_DT!", "!TRT_END_DT!", "!CLCACRE_ME!"], 
                          ['', '', ''])
        arcpy.CopyFeatures_management("RestorationTreatment_utm2", "RestorationTreatment_fc")
        add_and_calculate("RestorationTreatment_fc", ["perim", "newxtx", "newytx", "clcacretx_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT"], [20, 20, 20, 20], 
                          ["str(!SHAPE.LENGTH@METERS!)", "!newx!", "!newy!", "!CLCACRE_ME!"], 
                          ['', '', '', '']) 
        row_pairs = set()
        with arcpy.da.UpdateCursor("RestorationTreatment_fc", ["AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "txBDate", "txEDate", "PHNLGY_NM", "DPC_TX", "newx", "newy", "perim", "clcacretx_fc", "NOTES"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("RestorationTreatment_fc", "TRT_GUID", "GUID")
        arcpy.CalculateField_management("RestorationTreatment_fc", "TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        manfm = arcpy.FieldMappings()
        manfm.addTable(Outgdb + "\\TreatmentComponentLocation")
        arcpy.Append_management("RestorationTreatment_fc", Outgdb + "\\TreatmentComponentLocation", "NO_TEST", manfm)

        # Split out REST_CL_NM fields
        add_and_calculate("RestorationTreatment_fc", ["REST_CL_NM_fc", "txBDate_fc", "PHNLGY_NM_fc", "LOC_NM_fc", "RECORDER_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [30, 30, 20, 100, 50], 
                          ["!REST_CL_NM!", "!txBDate!", "!PHNLGY_NM!", "!LOC_NM!", "!RECORDER!"], 
                          ['', '', '', '', '']) 
        restbfm = arcpy.FieldMappings()
        restbfm.addTable("RestorationTreatment_utm2")
        restbfm.addTable("RestorationTreatment_fc")        
        restbfm.addTable("RestorationTreatment_fc")
        arcpy.SpatialJoin_analysis("RestorationTreatment_utm2", "RestorationTreatment_fc", "RestorationTreatmentData_spp", "JOIN_ONE_TO_MANY", "KEEP_COMMON", restbfm, "ARE_IDENTICAL_TO", "", "")
        with arcpy.da.UpdateCursor("RestorationTreatmentData_spp", "*", "\"REST_CL_NM\" <> \"REST_CL_NM_fc\" OR \"txBDate\" <> \"txBDate_fc\" OR \"PHNLGY_NM\" <> \"PHNLGY_NM_fc\" OR \"LOC_NM\" <> \"LOC_NM_fc\" OR \"RECORDER\" <> \"RECORDER_fc\" OR \"clcacretx\" <> \"clcacretx_fc\"") as cursor:
            for row in cursor:
                cursor.deleteRow()
        row_pairs = set()
        arcpy.CopyFeatures_management("RestorationTreatmentData_spp", "RestorationTreatmentData_restb")
        with arcpy.da.UpdateCursor("RestorationTreatmentData_restb",["REST_CL_NM","TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management("RestorationTreatmentData_restb","restb2")
        mancompfm = arcpy.FieldMappings()
        mancompfm.addTable(Outgdb + "\\RESTORATIONCOMPONENT")
        arcpy.Append_management("restb2", Outgdb + "\\RESTORATIONCOMPONENT", "NO_TEST", mancompfm)
        ResNum = 1
        for field in arcpy.ListFields("RestorationTreatmentData_restb", "REST_CL_NM*"):
            arcpy.Select_analysis("RestorationTreatmentData_restb", "restb3_" + str(ResNum), "\"" + field.name + "\"" + " IS NOT NULL")
            RecNum = arcpy.GetCount_management("restb3_" + str(ResNum)).getOutput(0)
            if int(RecNum) > 0:
                arcpy.CalculateField_management("restb3_" + str(ResNum), "REST_CL_NM", "!" + field.name + "!", "PYTHON3")
                ResNum += 1
        resfld = arcpy.ListFeatureClasses("restb3_*")
        arcpy.Append_management(resfld, "RestorationTreatmentData_restb")
        arcpy.Select_analysis("RestorationTreatmentData_restb", "RestorationTreatmentData_ressel", "\"REST_CL_NM\" IS NOT NULL")
        arcpy.CopyFeatures_management("RestorationTreatmentData_ressel", "RestorationTreatmentData_spp")
        rescnt = arcpy.GetCount_management("RestorationTreatmentData_ressel").getOutput(0)
        if int(rescnt) > 0:
            arcpy.row_pairs = set()
            with arcpy.da.UpdateCursor("RestorationTreatmentData_ressel", ["REST_CL_NM", "TRT_GUID"]) as cursor:
                for row in cursor:
                    row_pair = tuple(row)
                    if row_pair in row_pairs:
                        cursor.deleteRow()
                    else:
                        row_pairs.add(row_pair)
            arcpy.CopyRows_management("RestorationTreatmentData_ressel", "restb2")
            restcompfm = arcpy.FieldMappings()
            restcompfm.addTable(Outgdb + "\\RESTORATIONCOMPONENT")
            arcpy.Append_management("restb2", Outgdb + "\\RESTORATIONCOMPONENT", "NO_TEST", restcompfm)

        # Split out SCNTFC_CD fields
        treat_species_append("RestorationTreatmentData")

    # Set TreatmentData as workspace
    arcpy.env.workspace = workcopy + "\\TreatmentData"

    # Check for data in each Revegetation feature class
    arcpy.AddMessage("Processing revegetation treatment data.")
    project_albers_treat("Revegetation")

    # Buffer line and point data
    arcpy.env.workspace = "memory"
    buffer_lines_and_points("Revegetation")

    # Append all polygon files together
    arcpy.CreateFeatureclass_management(workcopy, "RevegetationTreatment_allpy", "POLYGON", workcopy + "\\TreatmentData\\RevegetationComponentPy", "", "", sralbers)
    PTPy = arcpy.ListFeatureClasses("Revegetation*Py_gcs")
    PTPyCt = len(PTPy)
    revpy = arcpy.FieldMappings()
    revpy.addTable(workcopy + "\\TreatmentData\\RevegetationComponentPy")    
    if PTPyCt > 0:
        arcpy.Append_management(PTPy, workcopy + "\\RevegetationTreatment_allpy", "NO_TEST", revpy)

        # Calculate State and County fields
        add_and_calculate(workcopy + "\\RevegetationTreatment_allpy", ["newx", "newy", "CNTR_PT_CN"], ["DOUBLE", "DOUBLE", "TEXT"], [0, 0, 50], ["!SHAPE.CENTROID.X!", "!SHAPE.CENTROID.Y!", "\"X: \" + str(!newx!) + \" Y: \" + str(!newy!)"], ['', '', ''])
        state_and_county("RevegetationTreatment")
        add_and_calculate("RevegetationTreatment_join", ["STATE_CD", "COUNTY_CD"], ["TEXT", "TEXT"], [2, 5], ["!STUSPS_1!", "!GEOID_1!"], ['', ''])

        # Convert UTC dates
        convert_utc_dates("RevegetationTreatment", "TRT_BEG_DT", "TRT_END_DT")            

        # Calculate acreages
        calculate_treat_acres("RevegetationTreatment")
        
        # Calculate LGCY_FL
        arcpy.AddField_management("RevegetationTreatment_utm2", "LGCY_FL", "TEXT", "", "", 1)
        arcpy.CalculateField_management("RevegetationTreatment_utm2", "LGCY_FL", "\"" + LgcySt + "\"")

        # Calculate CMP_TY_NM
        arcpy.AddField_management("RevegetationTreatment_utm2", "CMP_TY_NM", "TEXT", "", "", 20)
        arcpy.CalculateField_management("RevegetationTreatment_utm2", "CMP_TY_NM", "\"REVEGETATION\"")

        # Append to TreatmentComponentLocation
        add_and_calculate("RevegetationTreatment_utm2", ["rejoin_ct", "txBDate", "txEDate", "clcacretx"], 
                          ["LONG", "TEXT", "TEXT", "TEXT"], [0, 30, 30, 20], 
                          ["autoIncrement()", "!TRT_BEG_DT!", "!TRT_END_DT!", "!CLCACRE_ME!"], 
                          [count_cb, '', '', ''])
        arcpy.CopyFeatures_management("RevegetationTreatment_utm2", "RevegetationTreatment_fc")
        add_and_calculate("RevegetationTreatment_fc", ["perim", "stocktx", "newxtx", "newytx", "clcacretx_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT", "TEXT"], [20, 20, 20, 20, 20], 
                          ["str(!SHAPE.LENGTH@METERS!)", "!STOCK_ME!", "!newx!", "!newy!", "!CLCACRE_ME!"], 
                          ['', '', '', '', '']) 
        row_pairs = set()
        with arcpy.da.UpdateCursor("RevegetationTreatment_fc", ["AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "txBDate", "txEDate", "PHNLGY_NM", "DPC_TX", "stocktx", "VEG_UOM_NM", "REVEG_PHNLGY_NM", "SEEDLOT_NR", "RVG_SCNTFC_CD", "newx", "newy", "perim", "clcacretx_fc", "NOTES"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.AddField_management("RevegetationTreatment_fc", "TRT_GUID", "GUID")
        arcpy.CalculateField_management("RevegetationTreatment_fc", "TRT_GUID", "CalcGUID()", "PYTHON3", guid_cb)
        revfm = arcpy.FieldMappings()
        revfm.addTable(Outgdb + "\\TreatmentComponentLocation")
        arcpy.Append_management("RevegetationTreatment_fc", Outgdb + "\\TreatmentComponentLocation", "NO_TEST", revfm)

        # Merge to REVEGETATIONCOMPONENT
        arcpy.DeleteField_management("RevegetationTreatment_utm2", "VEG_UOM_NM_1; STOCK_ME_1; TRT_BEG_DT_1")
        arcpy.DeleteField_management("RevegetationTreatment_fc", "VEG_UOM_NM_1; STOCK_ME_1; TRT_BEG_DT_1")  
        add_and_calculate("RevegetationTreatment_utm2", ["stocktx", "txsdlt", "clcacretx"], 
                          ["TEXT", "TEXT", "TEXT"], [20, 20, 20], 
                          ["!STOCK_ME!", "!SEEDLOT_NR!", "!CLCACRE_ME!"], 
                          ['', '', ''])
        add_and_calculate("RevegetationTreatment_fc", ["txBDate_fc", "RVG_SCNTFC_CD_fc", "stocktx_fc", "txsdlt_fc"], 
                          ["TEXT", "TEXT", "TEXT", "TEXT"], [30, 10, 20, 20], 
                          ["!txBDate!", "!RVG_SCNTFC_CD!", "!STOCK_ME!", "!SEEDLOT_NR!"], 
                          ['', '', '', ''])             
        revtbfm = arcpy.FieldMappings()
        revtbfm.addTable("RevegetationTreatment_utm2")
        revtbfm.addTable("RevegetationTreatment_fc")
        arcpy.SpatialJoin_analysis("RevegetationTreatment_utm2", "RevegetationTreatment_fc", "RevegetationTreatmentData_spp", "JOIN_ONE_TO_MANY", "KEEP_COMMON", revtbfm, "ARE_IDENTICAL_TO", "", "")
        arcpy.Select_analysis("RevegetationTreatmentData_spp", "RevegetationTreatment_revtb", "\"txBDate\" = \"txBDate_fc\" AND \"RVG_SCNTFC_CD\" = \"RVG_SCNTFC_CD_fc\" AND \"stocktx\" = \"stocktx_fc\"")
        arcpy.Select_analysis("RevegetationTreatmentData_spp", "RevegetationTreatment_revtb2", "\"txBDate\" = \"txBDate_fc\" AND \"txsdlt\" = \"txsdlt_fc\"AND \"stocktx\" = \"stocktx_fc\"")
        arcpy.Append_management("RevegetationTreatment_revtb2", "RevegetationTreatment_revtb", "NO_TEST")
        row_pairs = set()
        with arcpy.da.UpdateCursor("RevegetationTreatment_revtb", ["stocktx", "VEG_UOM_NM", "PHNLGY_NM", "txsdlt", "RVG_SCNTFC_CD", "TRT_GUID"]) as cursor:
            for row in cursor:
                row_pair = tuple(row)
                if row_pair in row_pairs:
                    cursor.deleteRow()
                else:
                    row_pairs.add(row_pair)
        arcpy.CopyRows_management("RevegetationTreatment_revtb", "revtb3")
        revcompfm = arcpy.FieldMappings()
        revcompfm.addTable(Outgdb + "\\REVEGETATIONCOMPONENT")
        arcpy.Append_management("revtb3", Outgdb + "\\REVEGETATIONCOMPONENT", "NO_TEST", revcompfm)

        # Split out SCNTFC_CD fields
        treat_species_append("RevegetationTreatmentData")

    # Set workcopy as workspace
    arcpy.env.workspace = workcopy
                                
    # Check for data in photo feature class
    arcpy.AddMessage("Processing photo data.")
    fcct = arcpy.GetCount_management("PhotoLocation").getOutput(0)
    if int(fcct) > 0:
        fld_spatialref = arcpy.Describe("PhotoLocation").spatialReference
        if fld_spatialref != new_spatialref:
            arcpy.Project_management("PhotoLocation", "PhotoLocation_gcs", new_spatialref)
            arcpy.Delete_management("PhotoLocation")      
        else:
            arcpy.CopyFeatures_management("PhotoLocation", "PhotoLocation_gcs")
            arcpy.Delete_management("PhotoLocation")
        arcpy.CopyFeatures_management("PhotoLocation_gcs", "memory/PhotoLocation_gcs")

        arcpy.env.workspace = "memory"

        # Convert UTC dates
        if 'true' in TZDT:
            arcpy.CopyFeatures_management("PhotoLocation_gcs", "PhotoLocation_tz")
            arcpy.CopyRows_management(DMgdb + "\\DST", "DST")
            arcpy.DeleteIdentical_management("PhotoLocation_tz", "TIMEZONE")
            with arcpy.da.SearchCursor("PhotoLocation_tz", ["TIMEZONE", "DST"]) as cursor:
                for row in cursor:
                    tzval = str(row[0])
                    arcpy.Select_analysis("PhotoLocation_gcs", "PhotoLocation_tz" + str(tzval) + "_NoDST", "\"TIMEZONE\" = \'" + str(tzval) + "\' AND \"DST\" = \'FALSE\'")
                    recct = arcpy.GetCount_management("PhotoLocation_tz" + str(tzval) + "_NoDST").getOutput(0)
                    if int(recct) > 0:
                        arcpy.ConvertTimeZone_management("PhotoLocation_tz" + str(tzval)+ "_NoDST", "PHOTODATE", "UTC", "PHOTODATE_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")
                        arcpy.CalculateField_management("PhotoLocation_tz" + str(tzval)+ "_NoDST", begindt, "!PHOTODATE_temp!", "PYTHON3")
                    arcpy.Select_analysis("PhotoLocation_gcs", workcopy + "\\PhotoLocation_tz_" + str(tzval) + "_DST", "\"TIMEZONE\" = \'" + str(tzval) + "\' AND \"DST\" = \'TRUE\'")
                    recct = arcpy.GetCount_management(workcopy + "\\PhotoLocation_tz_" + str(tzval) + "_DST").getOutput(0)
                    if int(recct) > 0:
                        arcpy.AddField_management(workcopy + "\\PhotoLocation_tz_" + str(tzval) + "_DST", "DST_FL", "TEXT", "", "", 5)
                        dst_ranges = []
                        with arcpy.da.SearchCursor("DST", ["PHOTODATE"]) as cursor1:
                            for row1 in cursor1:
                                dst_ranges.append(row1[0])
                        with arcpy.da.UpdateCursor(workcopy + "\\PhotoLocation_tz_" + str(tzval) + "_DST", ["PHOTODATE", "DST_FL"]) as cursor2:
                            for row2 in cursor2:
                                phtdt = row2[0]
                                if row2[1] == 'FALSE' or row2[1] is None:
                                    is_dst = any(start <= phtdt <= end for start, end in dst_ranges)
                                    new_val = 'TRUE' if is_dst else 'FALSE'
                                    if row2[1] != new_val:
                                        row2[1] = new_val
                                        cursor2.updateRow(row2)
                    arcpy.Select_analysis(workcopy + "\\PhotoLocation_tz_" + str(tzval) + "_DST", fccat + "_tz_" + str(tzval) + "_NoDST2", "\"DST_FL\" = \'FALSE\'")
                    recct = arcpy.GetCount_management("PhotoLocation_tz_" + str(tzval) + "_NoDST2").getOutput(0)
                    if int(recct) > 0:
                        arcpy.ConvertTimeZone_management("PhotoLocation_tz_" + str(tzval) + "_NoDST2", begindt, "UTC", "PHOTODATE_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_NOT_ADJUSTED_FOR_DST")
                        arcpy.CalculateField_management("PhotoLocation_tz_" + str(tzval) + "_NoDST2", begindt, "!PHOTODATE_temp!", "PYTHON3")                            
                        arcpy.CopyFeatures_management("PhotoLocation_tz_" + str(tzval) + "_NoDST2", "PhotoLocation_tz_start_" + str(tzval) + "_NoDST2")
                        if enddt == 0:
                            arcpy.CopyFeatures_management("PhotoLocation_tz_start_" + str(tzval) + "_NoDST2", "PhotoLocation_tz_merge_" + str(tzval) + "_NoDST2")
                    arcpy.Select_analysis(workcopy + "\\PhotoLocation_tz_" + str(tzval) + "_DST", "PhotoLocation_tz_" + str(tzval) + "_YesDST", "\"DST_FL\" = \'TRUE\'")
                    recct = arcpy.GetCount_management("PhotoLocation_tz_" + str(tzval) + "_YesDST").getOutput(0)
                    if int(recct) > 0:
                        arcpy.ConvertTimeZone_management("PhotoLocation_tz_" + str(tzval) + "_YesDST", begindt, "UTC", "PHOTODATE_temp", tzval, "INPUT_NOT_ADJUSTED_FOR_DST", "OUTPUT_ADJUSTED_FOR_DST")
                        arcpy.CalculateField_management("PhotoLocation_tz_" + str(tzval) + "_YesDST", begindt, "!PHOTODATE_temp!", "PYTHON3")
                        arcpy.CopyFeatures_management("PhotoLocation_tz_" + str(tzval) + "_YesDST", "PhotoLocation_tz_start_" + str(tzval) + "_YesDST")          
            tzlist = arcpy.ListFeatureClasses("PhotoLocation_tz_merge_*")
            tzfm = arcpy.FieldMappings()
            tzfm = tzfm.addTable("PhotoLocation_gcs")
            arcpy.Merge_management(tzlist, "PhotoLocation_join", tzfm)
        else:
            arcpy.CopyFeatures_management("PhotoLocation_gcs", "PhotoLocation_join")

        # Calculate PHOTO_GUID
        arcpy.env.workspace = "memory"
        arcpy.AddField_management("PhotoLocation_join", "PHOTO_GUID", "GUID")
        arcpy.CalculateField_management("PhotoLocation_join", "PHOTO_GUID", "CalcGUID()", "PYTHON3", guid_cb)

        # Append to PhotoLocation
        photfm = arcpy.FieldMappings()
        photfm.addTable(Outgdb + "\\PhotoLocation")
        arcpy.Append_management("PhotoLocation_join", Outgdb + "\\PhotoLocation", "NO_TEST", photfm)

        # Split out PHOTOS
        PhNum = 1
        for field in arcpy.ListFields("PhotoLocation_join", "PHOTODATE*"):
            arcpy.Select_analysis("PhotoLocation_join", "Phototb_" + str(PhNum), "\"" + field.name + "\" IS NOT NULL")
            RecNum = arcpy.GetCount_management("Phototb_" + str(PhNum)).getOutput(0)
            if int(RecNum) > 0:
                arcpy.CalculateField_management("Phototb_" + str(PhNum), "PHOTODATE", "!" + field.name + "!", "PYTHON3")
                PhNR = str(field.name)
                PhNR = PhNR.strip("PHOTODATE")
                PhDeg = str("PHOTODEG" + PhNR)
                arcpy.CalculateField_management("Phototb_" + str(PhNum), "PHOTODEG", "!" + PhDeg + "!", "PYTHON3")
                PhPre = str("PREFIX" + PhNR)
                arcpy.CalculateField_management("Phototb_" + str(PhNum), "PREFIX", "!" + PhPre + "!", "PYTHON3")
                PhPNr = str("PHOTONUM" + PhNR)
                arcpy.CalculateField_management("Phototb_" + str(PhNum), "PHOTONUM", "!" + PhPNr + "!", "PYTHON3")
                PhPur = str("PURPOSE" + PhNR)
                arcpy.CalculateField_management("Phototb_" + str(PhNum), "PURPOSE", "!" + PhPur + "!", "PYTHON3")
                PhPh = str("PHOTO" + PhNR)
                arcpy.CalculateField_management("Phototb_" + str(PhNum), "PHOTO", "!" + PhPh + "!", "PYTHON3")
                PhNum += 1
        arcpy.CreateFeatureclass_management("memory", "PhotoLocation_copy", "POINT", "PhotoLocation_join", "", "", new_spatialref)
        phfld = arcpy.ListFeatureClasses("Phototb_*")
        arcpy.Append_management(phfld, "PhotoLocation_copy", "NO_TEST")
        arcpy.Select_analysis("PhotoLocation_copy", "PhotoLocation_sel", "\"PHOTODATE\" IS NOT NULL")
        phcnt = arcpy.GetCount_management("PhotoLocation_sel").getOutput(0)
        if int(phcnt) > 0:
            arcpy.CopyRows_management("PhotoLocation_sel", "pht_all")
            phottbfm = arcpy.FieldMappings()
            phottbfm.addTable(Outgdb + "\\PHOTOS")
            arcpy.Append_management("pht_all", Outgdb + "\\PHOTOS", "NO_TEST", phottbfm)

except:

    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n      " + str(sys.exc_info()[1])
    msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    arcpy.AddError(msgs)
    arcpy.AddError(pymsg)

arcpy.Delete_management("memory")
 
