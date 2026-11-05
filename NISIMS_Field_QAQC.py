#----------------------------------------------------------------------------------------------------------------------
# Name: NISIMS_Field_QAQC.py
# Purpose: This script was created to automate the quality checking process conducted by the NISIMS data manager.
# Author: Jennifer Sieracki
# Created: 2018-05-31
# Updated: 2025-12-31
#----------------------------------------------------------------------------------------------------------------------

# Import modules
import arcpy, sys, traceback, time, datetime

#Input variables
InField = arcpy.GetParameterAsText(0)
InAdmin = arcpy.GetParameterAsText(1)
OutLoc = arcpy.GetParameterAsText(2)
OutFile = arcpy.GetParameterAsText(3)


# Define variables
Report = OutLoc + "\\" + OutFile + "_QCReport_" + str(time.strftime("%m%d%Y")) + ".txt"
SppLst = OutLoc + "\\" + OutFile + "_SppList_" + str(time.strftime("%m%d%Y")) + ".txt"
TotCt = OutLoc + "\\" + OutFile + "_RecCount_" + str(time.strftime("%m%d%Y")) + ".txt"

try:
    # Set workspace and open text files
    arcpy.env.workspace = InField
    err = open(Report, "w")
    spp = open(SppLst, "w")
    cts = open(TotCt, "w")
    wsloc = wsspp = 0
    wiloc = wilu = 0
    pbioloc = pbiospp = pbioag = pbiocp = pbionepa = pchemloc = pchemspp = pchemag = pchemcp = pchemnepa = pothloc = pothspp = pothcp = pothnepa = 0
    bioloc = biospp = chemloc = chemspp = chemag = chemadj = firloc = firspp = manloc = manspp = mechloc = mechspp = revloc = revspp = resloc = resspp = resact = 0
    photloc = phot = 0

    # Copy feature classes into unlocked copy of field geodatabase
    arcpy.Copy_management(InAdmin + "\\DM_NISIMS_Field.gdb", OutLoc + "\\workcopy.gdb")
    for fc in arcpy.ListFeatureClasses():
        arcpy.AddMessage("Are you running just feature classes?")
        if "PhotoLocation" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\PhotoLocation", "NO_TEST")
        elif "ProposedBiologicalTreatmentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedBiologicalTreatmentLn", "NO_TEST")
        elif "ProposedBiologicalTreatmentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedBiologicalTreatmentPt", "NO_TEST")
        elif "ProposedBiologicalTreatmentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedBiologicalTreatmentPy", "NO_TEST")
        elif "ProposedChemicalTreatmentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedChemicalTreatmentLn", "NO_TEST")
        elif "ProposedChemicalTreatmentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedChemicalTreatmentPt", "NO_TEST")
        elif "ProposedChemicalTreatmentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedChemicalTreatmentPy", "NO_TEST")
        elif "ProposedOtherTreatmentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedOtherTreatmentLn", "NO_TEST")
        elif "ProposedOtherTreatmentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedOtherTreatmentPt", "NO_TEST")
        elif "ProposedOtherTreatmentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedOtherTreatmentPy", "NO_TEST")
        elif "BiologicalComponentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\BiologicalComponentLn", "NO_TEST")         
        elif "BiologicalComponentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\BiologicalComponentPt", "NO_TEST")
        elif "BiologicalComponentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\BiologicalComponentPy", "NO_TEST")
        elif "ChemicalComponentLn" in fc:
            for field in arcpy.ListFields(fc, "CARR*"):
                if "CARRVOL_ME" in field.name:
                    arcpy.AddField_management(fc, "MIXVOL_ME", "DOUBLE")
                    arcpy.CalculateField_management(fc, "MIXVOL_ME", "!CARRVOL_ME!", "PYTHON_9.3")
                    arcpy.DeleteField_management(fc, "CARRVOL_ME")

                elif "CARRUOM_NM" in field.name:
                    arcpy.AddField_management(fc, "MIXUOM_NM", "TEXT", "", "", 40)
                    arcpy.CalculateField_management(fc, "MIXUOM_NM", "!CARRUOM_NM!", "PYTHON_9.3")
                    arcpy.DeleteField_management(fc, "CARRUOM_NM")
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ChemicalComponentLn", "NO_TEST")            
        elif "ChemicalComponentPt" in fc:
            for field in arcpy.ListFields(fc, "CARR*"):
                if "CARRVOL_ME" in field.name:
                    arcpy.AddField_management(fc, "MIXVOL_ME", "DOUBLE")
                    arcpy.CalculateField_management(fc, "MIXVOL_ME", "!CARRVOL_ME!", "PYTHON_9.3")
                    arcpy.DeleteField_management(fc, "CARRVOL_ME")
                elif "CARRUOM_NM" in field.name:
                    arcpy.AddField_management(fc, "MIXUOM_NM", "TEXT", "", "", 40)
                    arcpy.CalculateField_management(fc, "MIXUOM_NM", "!CARRUOM_NM!", "PYTHON_9.3")
                    arcpy.DeleteField_management(fc, "CARRUOM_NM")
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ChemicalComponentPt", "NO_TEST")
        elif "ChemicalComponentPy" in fc:
            for field in arcpy.ListFields(fc, "CARR*"):
                if "CARRVOL_ME" in field.name:
                    arcpy.AddField_management(fc, "MIXVOL_ME", "DOUBLE")
                    arcpy.CalculateField_management(fc, "MIXVOL_ME", "!CARRVOL_ME!", "PYTHON_9.3")
                    arcpy.DeleteField_management(fc, "CARRVOL_ME")
                elif "CARRUOM_NM" in field.name:
                    arcpy.AddField_management(fc, "MIXUOM_NM", "TEXT", "", "", 40)
                    arcpy.CalculateField_management(fc, "MIXUOM_NM", "!CARRUOM_NM!", "PYTHON_9.3")
                    arcpy.DeleteField_management(fc, "CARRUOM_NM")
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ChemicalComponentPy", "NO_TEST")
        elif "FireComponentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\FireComponentLn", "NO_TEST")
        elif "FireComponentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\FireComponentPt", "NO_TEST")
        elif "FireComponentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\FireComponentPy", "NO_TEST")
        elif "ManualComponentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ManualComponentLn", "NO_TEST")
        elif "ManualComponentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ManualComponentPt", "NO_TEST")
        elif "ManualComponentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ManualComponentPy", "NO_TEST")
        elif "MechanicalComponentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\MechanicalComponentLn", "NO_TEST")
        elif "MechanicalComponentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\MechanicalComponentPt", "NO_TEST")
        elif "MechanicalComponentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\MechanicalComponentPy", "NO_TEST")
        elif "RestorationComponentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RestorationComponentLn", "NO_TEST")
        elif "RestorationComponentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RestorationComponentPt", "NO_TEST")
        elif "RestorationComponentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RestorationComponentPy", "NO_TEST")
        elif "RevegetationComponentLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RevegetationComponentLn", "NO_TEST")
        elif "RevegetationComponentPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RevegetationComponentPt", "NO_TEST")
        elif "RevegetationComponentPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RevegetationComponentPy", "NO_TEST")
        elif "WeedInfestationLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedInfestationData\\WeedInfestationLn", "NO_TEST")
        elif "WeedInfestationPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedInfestationData\\WeedInfestationPt", "NO_TEST")
        elif "WeedInfestationPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedInfestationData\\WeedInfestationPy", "NO_TEST")
        elif "WeedSurveyLn" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedSurveyData\\WeedSurveyLn", "NO_TEST")
        elif "WeedSurveyPt" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedSurveyData\\WeedSurveyPt", "NO_TEST")
        elif "WeedSurveyPy" in fc:
            arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedSurveyData\\WeedSurveyPy", "NO_TEST")
    for ds in arcpy.ListDatasets():
        arcpy.AddMessage("Dataset: " + str(ds))
        arcpy.env.workspace = ds
        for fc in arcpy.ListFeatureClasses():
            arcpy.AddMessage("Or are you getting into the datasets?")
            if "PhotoLocation" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\PhotoLocation", "NO_TEST")
            elif "ProposedBiologicalTreatmentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedBiologicalTreatmentLn", "NO_TEST")                
            elif "ProposedBiologicalTreatmentPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedBiologicalTreatmentPt", "NO_TEST")
            elif "ProposedBiologicalTreatmentPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedBiologicalTreatmentPy", "NO_TEST")
            elif "ProposedChemicalTreatmentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedChemicalTreatmentLn", "NO_TEST")
            elif "ProposedChemicalTreatmentPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedChemicalTreatmentPt", "NO_TEST")
            elif "ProposedChemicalTreatmentPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedChemicalTreatmentPy", "NO_TEST")
            elif "ProposedOtherTreatmentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedOtherTreatmentLn", "NO_TEST")
            elif "ProposedOtherTreatmentPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedOtherTreatmentPt", "NO_TEST")
            elif "ProposedOtherTreatmentPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\ProposedTreatmentData\\ProposedOtherTreatmentPy", "NO_TEST")
            elif "BiologicalComponentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\BiologicalComponentLn", "NO_TEST")                
            elif "BiologicalComponentPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\BiologicalComponentPt", "NO_TEST")
            elif "BiologicalComponentPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\BiologicalComponentPy", "NO_TEST")
            elif "ChemicalComponentLn" in fc:
                for field in arcpy.ListFields(fc, "CARR*"):
                    if "CARRVOL_ME" in field.name:
                        arcpy.AddField_management(fc, "MIXVOL_ME", "DOUBLE")
                        arcpy.CalculateField_management(fc, "MIXVOL_ME", "!CARRVOL_ME!", "PYTHON_9.3")
                        arcpy.DeleteField_management(fc, "CARRVOL_ME")
                    elif "CARRUOM_NM" in field.name:
                        arcpy.AddField_management(fc, "MIXUOM_NM", "TEXT", "", "", 40)
                        arcpy.CalculateField_management(fc, "MIXUOM_NM", "!CARRUOM_NM!", "PYTHON_9.3")
                        arcpy.DeleteField_management(fc, "CARRUOM_NM")                
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ChemicalComponentLn", "NO_TEST")
            elif "ChemicalComponentPt" in fc:
                arcpy.AddMessage("Appending: " + str(fc))
                for field in arcpy.ListFields(fc, "CARR*"):
                    if "CARRVOL_ME" in field.name:
                        arcpy.AddField_management(fc, "MIXVOL_ME", "DOUBLE")
                        arcpy.CalculateField_management(fc, "MIXVOL_ME", "!CARRVOL_ME!", "PYTHON_9.3")
                        arcpy.DeleteField_management(fc, "CARRVOL_ME")
                    elif "CARRUOM_NM" in field.name:
                        arcpy.AddField_management(fc, "MIXUOM_NM", "TEXT", "", "", 40)
                        arcpy.CalculateField_management(fc, "MIXUOM_NM", "!CARRUOM_NM!", "PYTHON_9.3")
                        arcpy.DeleteField_management(fc, "CARRUOM_NM")
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ChemicalComponentPt", "NO_TEST")
            elif "ChemicalComponentPy" in fc:
                for field in arcpy.ListFields(fc, "CARR*"):
                    if "CARRVOL_ME" in field.name:
                        arcpy.AddField_management(fc, "MIXVOL_ME", "DOUBLE")
                        arcpy.CalculateField_management(fc, "MIXVOL_ME", "!CARRVOL_ME!", "PYTHON_9.3")
                        arcpy.DeleteField_management(fc, "CARRVOL_ME")
                    elif "CARRUOM_NM" in field.name:
                        arcpy.AddField_management(fc, "MIXUOM_NM", "TEXT", "", "", 40)
                        arcpy.CalculateField_management(fc, "MIXUOM_NM", "!CARRUOM_NM!", "PYTHON_9.3")
                        arcpy.DeleteField_management(fc, "CARRUOM_NM")
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ChemicalComponentPy", "NO_TEST")
            elif "FireComponentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\FireComponentLn", "NO_TEST")
            elif "FireComponentPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\FireComponentPt", "NO_TEST")
            elif "FireComponentPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\FireComponentPy", "NO_TEST")
            elif "ManualComponentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ManualComponentLn", "NO_TEST")
            elif "ManualComponentPt" in fc:
                arcpy.AddMessage("Appending: " + str(fc))
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ManualComponentPt", "NO_TEST")
            elif "ManualComponentPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\ManualComponentPy", "NO_TEST")
            elif "MechanicalComponentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\MechanicalComponentLn", "NO_TEST")
            elif "MechanicalComponentPt" in fc:
                arcpy.AddMessage("Appending: " + str(fc))
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\MechanicalComponentPt", "NO_TEST")
            elif "MechanicalComponentPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\MechanicalComponentPy", "NO_TEST")
            elif "RestorationComponentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RestorationComponentLn", "NO_TEST")
            elif "RestorationComponentPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RestorationComponentPt", "NO_TEST")
            elif "RestorationComponentPy" in fc:
                arcpy.AddMessage("Appending: " + str(fc))
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RestorationComponentPy", "NO_TEST")                
            elif "RevegetationComponentLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RevegetationComponentLn", "NO_TEST")
            elif "RevegetationComponentPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RevegetationComponentPt", "NO_TEST")
            elif "RevegetationComponentPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\TreatmentData\\RevegetationComponentPy", "NO_TEST")
            elif "WeedInfestationLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedInfestationData\\WeedInfestationLn", "NO_TEST")
            elif "WeedInfestationPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedInfestationData\\WeedInfestationPt", "NO_TEST")
            elif "WeedInfestationPy" in fc:
                arcpy.AddMessage("Appending: " + str(fc))
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedInfestationData\\WeedInfestationPy", "NO_TEST")
            elif "WeedSurveyLn" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedSurveyData\\WeedSurveyLn", "NO_TEST")
            elif "WeedSurveyPt" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedSurveyData\\WeedSurveyPt", "NO_TEST")
            elif "WeedSurveyPy" in fc:
                arcpy.Append_management(fc, OutLoc + "\\workcopy.gdb\\WeedSurveyData\\WeedSurveyPy", "NO_TEST")
        arcpy.env.workspace = InField

    # Copy feature classes into memory
    arcpy.env.workspace = OutLoc + "\\workcopy.gdb"
    for fc in arcpy.ListFeatureClasses():
        arcpy.CopyFeatures_management(fc, "memory\\" + fc)
    for ds in arcpy.ListDatasets():
        arcpy.env.workspace = ds
        for fc in arcpy.ListFeatureClasses():
            arcpy.CopyFeatures_management(fc, "memory\\" + fc)
        arcpy.env.workspace = OutLoc + "\\workcopy.gdb"

    # Reset workspace to memory
    arcpy.env.workspace = "memory"

    # QC for all feature classes
    for fc in arcpy.ListFeatureClasses():
        arcpy.AddMessage("Line 264: " + str(fc))
        err.write("\n" + fc + "\n")
        spp.write("\n" + fc + "\n")
        desc = arcpy.Describe(fc)
        recct = arcpy.GetCount_management(fc).getOutput(0)
        if int(recct) == 0:
            err.write("WARNING: " + fc + " contains 0 records.\n")
        else:
            in_spatialref = arcpy.Describe(fc).spatialreference
            if in_spatialref == "Unknown":
                err.write("ERROR: " + fc + " is missing spatial reference.\n")
            arcpy.RepairGeometry_management(fc)
            for field in arcpy.ListFields(fc, "*", "String"):
                fldnm = str(field.name)
                arcpy.CalculateField_management(fc, fldnm, "!" + fldnm + "!.strip()", "PYTHON_9.3")

            # QC for all but photo points
            if "PhotoLocation" not in fc:
                ## Check for location and recorder values
                arcpy.Select_analysis(fc, fc + "_locnm", "\"LOC_NM\" IS NULL OR \"LOC_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                recct = arcpy.GetCount_management(fc + "_locnm").getOutput(0)
                if int(recct) > 0:
                    err.write("ERROR: " + fc + ":LOC_NM is missing values. LOC_NM is a required field. Ensure that no fields are empty or populated with \"none\", \"NA\", or anything similar.\n")
                arcpy.Select_analysis(fc, fc + "_rec", "\"RECORDER\" IS NULL OR \"RECORDER\" IN ('none', 'None', 'NONE', ' ', '')")
                recct = arcpy.GetCount_management(fc + "_rec").getOutput(0)
                if int(recct) > 0:
                    err.write("ERROR: " + fc + ":RECORDER is missing values. RECORDER is a required field. Ensure that no fields are empty or populated with \"none\", or anything similar.\n")
                ## Check USDA Plants codes
                arcpy.Select_analysis(fc, fc + "_spp", "\"SCNTFC_CD\" IS NULL OR \"SCNTFC_CD\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                recct = arcpy.GetCount_management(fc + "_spp").getOutput(0)
                if int(recct) > 0:
                    err.write("ERROR: " + fc + ":SCNTFC_CD is missing values. SCNTFC_CD is a required field. Ensure that no fields are empty or populated with \"none\", or anything similar.\n")                    
                fldct = 1     
                for field in arcpy.ListFields(fc, "SCNTFC_CD*"):
                    arcpy.Select_analysis(fc, fc + "_spplst" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                    recct = arcpy.GetCount_management(fc + "_spplst" + str(fldct)).getOutput(0)
                    if int(recct) > 0:
                        arcpy.JoinField_management(fc + "_spplst" + str(fldct), field.name, InAdmin + "\\NISIMS.gdb\\domSCNTFC_CD", "SPPCD", "SPPCD")
                        arcpy.Select_analysis(fc + "_spplst" + str(fldct), fc + "_badspp" + str(fldct), "\"SPPCD\" IS NULL AND \"" + field.name + "\" IS NOT NULL")
                        if int(fldct) > 1:
                            arcpy.CalculateField_management(fc + "_badspp" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                        fldct += 1                    
                sppmap = arcpy.FieldMappings()
                sppmap.addTable(fc)
                fclst = arcpy.ListFeatureClasses(fc + "_badspp*")
                arcpy.Merge_management(fclst, fc + "_sppall", sppmap)
                recct = arcpy.GetCount_management(fc + "_sppall").getOutput(0)
                if int(recct) > 0:
                    arcpy.DeleteIdentical_management(fc + "_sppall", ["SCNTFC_CD"])
                    with arcpy.da.SearchCursor(fc + "_sppall", ["SCNTFC_CD"]) as cursor:
                        for row in cursor:
                            sppval = str(row[0])
                            spp.write("WARNING: " + sppval + " is not on the species list.\n")
                ## Check team values
                arcpy.Select_analysis(fc, fc + "_tmnull", "\"TEAM\" IS NULL OR \"TEAM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                recct = arcpy.GetCount_management(fc + "_tmnull").getOutput(0)
                if int(recct) > 0:
                    err.write("ERROR: " + fc + ":TEAM is missing values. TEAM is a required field. Ensure that no fields are empty or populated with \"none\", or anything similar.\n")
                arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "domTeam", InAdmin + "\\NISIMS.gdb\\domTEAM", "TEAM_CD", "DESC")
                arcpy.Select_analysis(fc, fc + "_tmnotnull", "\"TEAM\" IS NOT NULL AND \"TEAM\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                arcpy.JoinField_management(fc + "_tmnotnull", "TEAM", InAdmin + "\\NISIMS.gdb\\domTEAM", "TEAM_CD", "TEAM_CD")
                arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domTEAM")
                arcpy.Select_analysis(fc + "_tmnotnull", fc + "_team", "\"TEAM_CD\" IS NULL")
                recct = arcpy.GetCount_management(fc + "_team").getOutput(0)
                if int(recct) > 0:
                    arcpy.DeleteIdentical_management(fc + "_team", ["TEAM"])
                    with arcpy.da.SearchCursor(fc + "_team", ["TEAM"]) as cursor:
                        for row in cursor:
                            tmval = str(row[0])
                            err.write("WARNING: " + tmval + " is not an approved team name for " + fc + ". If this is a park team, please ignore. If this is a contractor, be sure the EPMT name is at the beginning of the team name.\n")
                ## Check park unit values
                arcpy.Select_analysis(fc, fc + "_pknull", "\"PARK_UNIT\" IS NULL OR \"PARK_UNIT\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                recct = arcpy.GetCount_management(fc + "_pknull").getOutput(0)
                if int(recct) > 0:
                    err.write("ERROR: " + fc + ":PARK_UNIT is missing values. PARK_UNIT is a required field. Ensure that no fields are empty or populated with \"none\", or anything similar.\n")
                arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "domParkUnit", InAdmin + "\\NISIMS.gdb\\domPARK_UNIT", "PARK_UNIT_CD", "DESC")
                arcpy.Select_analysis(fc, fc + "pknotnull", "\"PARK_UNIT\" IS NOT NULL AND \"PARK_UNIT\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                arcpy.JoinField_management(fc + "pknotnull", "PARK_UNIT", InAdmin + "\\NISIMS.gdb\\domPARK_UNIT", "PARK_UNIT_CD", "PARK_UNIT_CD")
                arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domPARK_UNIT")                
                arcpy.Select_analysis(fc + "pknotnull", fc + "_park", "\"PARK_UNIT_CD\" IS NULL")
                recct = arcpy.GetCount_management(fc + "_park").getOutput(0)
                if int(recct) > 0:
                    arcpy.DeleteIdentical_management(fc + "_park", ["PARK_UNIT"])
                    with arcpy.da.SearchCursor(fc + "_park", ["PARK_UNIT"]) as cursor:
                        for row in cursor:
                            prkval = str(row[0])
                            err.write("ERROR: " + prkval + " is not an approved park unit code for " + fc + ".\n")

                # QC for line feature classes
                if 'Polyline' in desc.shapeType:
                    arcpy.Select_analysis(fc, fc + "_bufm", "\"BUFFER_M\" IS NULL OR \"BUFFER_M\" = 0")
                    recct = arcpy.GetCount_management(fc + "_bufm").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BUFFER_M is missing values. BUFFER_M is a required field.\n")
                    arcpy.Select_analysis(fc, fc + "_bufdirnull", "\"BUFDIR\" IS NULL OR \"BUFDIR\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                    recct = arcpy.GetCount_management(fc + "_bufdirnull").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BUFDIR is missing values. BUFDIR is a required field for line features. Ensure that no fields are empty or populated with \"none\", or anything similar.\n")                    
                    arcpy.Select_analysis(fc, fc + "_bufdirnotnull", "\"BUFDIR\" IS NOT NULL AND \"BUFDIR\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                    arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "domBUFDIR", InAdmin + "\\NISIMS.gdb\\domBUFDIR", "BUFDIR_CD", "DESC")                        
                    arcpy.JoinField_management(fc + "_bufdirnotnull", "BUFDIR", InAdmin + "\\NISIMS.gdb\\domBUFDIR", "BUFDIR_CD", "BUFDIR_CD")
                    arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domBUFDIR")                
                    arcpy.Select_analysis(fc + "_bufdirnotnull", fc + "_bufd", "\"BUFDIR_CD\" IS NULL")
                    recct = arcpy.GetCount_management(fc + "_bufd").getOutput(0)
                    if int(recct) > 0:
                        arcpy.DeleteIdentical_management(fc + "_bufd", ["BUFDIR"])
                        with arcpy.da.SearchCursor(fc + "_bufd", "BUFDIR") as cursor:
                            for row in cursor:
                                bufval = str(row[0])
                                err.write("ERROR: " + bufval + " is not a valid buffer direction for " + fc + ".\n")

                # QC for point feature classes
                if 'Point' in desc.shapeType:
                    arcpy.Select_analysis(fc, fc + "_bufm", "\"BUFFER_M\" IS NULL OR \"BUFFER_M\" = 0")
                    recct = arcpy.GetCount_management(fc + "_bufm").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BUFFER_M is missing values. BUFFER_M is a required field.\n")

                # QC for Weed Survey data
                if "WeedSurvey" in fc:
                    arcpy.Select_analysis(fc, fc + "_bdtnull", "\"BEGIN_DT\" IS NULL")
                    recct = arcpy.GetCount_management(fc + "_bdtnull").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BEGIN_DT is missing values. BEGIN_DT is a required field.\n")
                    arcpy.Select_analysis(fc, fc + "_bdtnotnull", "\"BEGIN_DT\" IS NOT NULL")
                    arcpy.AddField_management(fc + "_bdtnotnull", "tempdt", "DATE")
                    arcpy.CalculateField_management(fc + "_bdtnotnull", "tempdt", "datetime.datetime.now()", "PYTHON_9.3")
                    arcpy.Select_analysis(fc + "_bdtnotnull", fc + "_bdtfut", "\"BEGIN_DT\" > \"tempdt\"")
                    recct = arcpy.GetCount_management(fc + "_bdtfut").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BEGIN_DT contains future dates.\n")
                    arcpy.AddField_management(fc + "_bdtnotnull", "dtstatus", "TEXT", "", "", 30)
                    arcpy.CalculateField_management(fc + "_bdtnotnull", "dtstatus", "str(!BEGIN_DT!)", "PYTHON_9.3")
                    arcpy.Select_analysis(fc + "_bdtnotnull", fc + "_bdttm", "\"dtstatus\" NOT LIKE '%-%' AND \"dtstatus\" NOT LIKE '%/%'")
                    recct = arcpy.GetCount_management(fc + "_bdttm").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BEGIN_DT contains invalid values.\n")
                    arcpy.Select_analysis(fc + "_bdtnotnull", fc + "_endbef", "\"BEGIN_DT\" > \"END_DT\" AND \"END_DT\" IS NOT NULL")
                    recct = arcpy.GetCount_management(fc + "_endbef").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: "  + fc + ":BEGIN_DT occurs after END_DT.\n")
                    # Get counts of Weed Survey data
                    arcpy.CopyFeatures_management(fc, fc + "_count")
                    arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "BEGIN_DT", "END_DT", "WSA_TY_NM", "LOC_NM", "PARK_UNIT", "RECORDER", "TEAM", "CLIENT"])
                    recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                    wsloc += int(recct)
                    arcpy.CopyFeatures_management(fc, fc + "_sppct")
                    fldct = 1
                    for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                        arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        if int(fldct) > 1:
                            arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                        fldct += 1
                    wssppfm = arcpy.FieldMappings()
                    wssppfm.addTable(fc + "_sppct")
                    fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                    arcpy.Merge_management(fclst, fc + "_spptot", wssppfm)
                    arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "BEGIN_DT", "END_DT", "WSA_TY_NM", "LOC_NM", "PARK_UNIT", "RECORDER", "TEAM", "CLIENT", "SCNTFC_CD"])
                    recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                    wsspp += int(recct)

                # QC for Weed Infestation data
                if "WeedInfestation" in fc:
                    arcpy.Select_analysis(fc, fc + "_cvrnull", "\"EST_CVR_RT\" IS NULL")
                    recct = arcpy.GetCount_management(fc + "_cvrnull").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":EST_CVR_RT is missing values. EST_CVR_RT is a required field.\n")
                    arcpy.Select_analysis(fc, fc + "_cvrzero", "\"EST_CVR_RT\" = 0")
                    recct = arcpy.GetCount_management(fc + "_cvrzero").getOutput(0)
                    if int(recct) > 0:
                        err.write("WARNING: " + fc + ":EST_CVR_RT includes 0 values. These will be deleted when being process.\n")
                    arcpy.Select_analysis(fc, fc + "_pres", "\"EST_CVR_RT\" > 0")
                    arcpy.Select_analysis(fc + "_pres", fc + "_bdtnull", "\"BEGIN_DT\" IS NULL")
                    recct = arcpy.GetCount_management(fc + "_bdtnull").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BEGIN_DT is missing values. BEGIN_DT is a required field.\n")
                    arcpy.Select_analysis(fc, fc + "_bdtnotnull", "\"BEGIN_DT\" IS NOT NULL")
                    arcpy.AddField_management(fc + "_bdtnotnull", "tempdt", "DATE")
                    arcpy.CalculateField_management(fc + "_bdtnotnull", "tempdt", "datetime.datetime.now()", "PYTHON_9.3")
                    arcpy.Select_analysis(fc + "_bdtnotnull", fc + "_bdtfut", "\"BEGIN_DT\" > \"tempdt\"")
                    recct = arcpy.GetCount_management(fc + "_bdtfut").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BEGIN_DT contains future dates.\n")
                    arcpy.AddField_management(fc + "_bdtnotnull", "dtstatus", "TEXT", "", "", 30)
                    arcpy.CalculateField_management(fc + "_bdtnotnull", "dtstatus", "str(!BEGIN_DT!)", "PYTHON_9.3")                        
                    arcpy.Select_analysis(fc + "_bdtnotnull", fc + "_bdttm", "\"dtstatus\" NOT LIKE '%-%' AND \"dtstatus\" NOT LIKE '%/%'")
                    recct = arcpy.GetCount_management(fc + "_bdttm").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":BEGIN_DT contains invalid values.\n")
                    arcpy.Select_analysis(fc + "_pres", fc + "_qty", "\"INFSTN_QY\" IS NOT NULL AND (\"QY_UOM_NM\" IS NULL OR \"QY_UOM_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na'))")
                    recct = arcpy.GetCount_management(fc + "_qty").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":QY_UOM_NM is missing values. QY_UOM_NM is required if INFSTN_QY is populated.\n")
                    # Get counts of Weed Infestation data
                    arcpy.CopyFeatures_management(fc, fc + "_count")
                    arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "BEGIN_DT", "EST_CVR_RT", "LOC_NM", "QT_MTHD_TX", "INFSTN_QY", "QY_UOM_NM", "PHNLGY_NM", "PHYSLMT_TX", "ACSMODE_NM", "SCNTFC_CD", "LOC_NM"])
                    recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                    wiloc += int(recct)
                    arcpy.CopyFeatures_management(fc, fc + "_luct")
                    fldct = 1
                    for field in arcpy.ListFields(fc + "_luct", "LU_CTGY_NM*"):
                        arcpy.Select_analysis(fc + "_luct", fc + "_selluct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        if int(fldct) > 1:
                            arcpy.CalculateField_management(fc + "_selluct" + str(fldct), "LU_CTGY_NM", "!" + field.name + "!", "PYTHON_9.3")
                        fldct += 1
                    wilufm = arcpy.FieldMappings()
                    wilufm.addTable(fc + "_luct")
                    fclst = arcpy.ListFeatureClasses(fc + "_selluct*")
                    arcpy.Merge_management(fclst, fc + "_lutot", wilufm)
                    arcpy.DeleteIdentical_management(fc + "_lutot", ["SHAPE", "EST_CVR_RT", "QT_MTHD_TX", "INFSTN_QY", "QY_UOM_NM", "PHNLGY_NM", "PHYSLMT_TX", "ACSMODE_NM", "SCNTFC_CD", "LOC_NM", "LU_CTGY_NM"])
                    recct = arcpy.GetCount_management(fc + "_lutot").getOutput(0)
                    wilu += int(recct)

                # QC for all Proposed Treatment data
                if "Proposed" in fc:
                    arcpy.Select_analysis(fc, fc + "_pdtnull", "\"PRP_DATE\" IS NULL")
                    recct = arcpy.GetCount_management(fc + "_pdtnull").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":PRP_DATE is missing values. PRP_DATE is a required field.\n")
                    arcpy.Select_analysis(fc, fc + "_pdtnotnull", "\"PRP_DATE\" IS NOT NULL")
                    arcpy.AddField_management(fc + "_pdtnotnull", "dtstatus", "TEXT", "", "", 30)
                    arcpy.CalculateField_management(fc + "_pdtnotnull", "dtstatus", "str(!PRP_DATE!)", "PYTHON_9.3")
                    arcpy.Select_analysis(fc + "_pdtnotnull", fc + "_pdttm", "\"dtstatus\" NOT LIKE '%-%' AND \"dtstatus\" NOT LIKE '%/%'")
                    recct = arcpy.GetCount_management(fc + "_pdttm").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":PRP_DATE contains invalid values.\n")
                    # QC for Proposed Biological Treatment data
                    if "Biological" in fc:
                        arcpy.Select_analysis(fc, fc + "_ag", "\"BIO_SCNTFC_CD\" IS NULL OR \"BIO_SCNTFC_CD\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_ag").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":BIO_SCNTFC_CD is missing values. BIO_SCNTFC_CD is a required field.\n")
                        fldct = 1
                        for field in arcpy.ListFields(fc, "BIO_SCNTFC_CD*"):
                            arcpy.Select_analysis(fc, fc + "_agnotnull", "\"" + field.name + "\" IS NOTNULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            arcpy.JoinField_management(fc + "_agnotnull", field, InAdmin + "\\NISIMS.gdb\\domApprovBioControl", "SPPCD", "SPPCD")
                            arcpy.Select_analysis(fc + "_agnotnull", fc + "_pbag" + str(fldct), "\"SPPCD\" IS NULL AND \"BIO_SCNTFC_CD\" IS NOT NULL")
                            arcpy.DeleteField_management(fc + "_agnotnull", "SPPCD")
                            if int(fldct) > 1:
                                arcpy.CalculateFields_management(fc + "_pbag" + str(fldct), "BIO_SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1                    
                        sppmap = arcpy.FieldMappings()
                        sppmap.addInputField(fc, "BIO_SCNTFC_CD")
                        fclst = arcpy.ListFeatureClasses(fc + "_pbag*")
                        arcpy.Merge_management(fclst, fc + "_pbspp", sppmap)
                        recct = arcpy.GetCount_management(fc + "_pbspp").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_pbspp", ["BIO_SCNTFC_CD"])
                            with arcpy.da.SearchCursor(fc + "_pbspp", ["BIO_SCNTFC_CD"]) as cursor:
                                for row in cursor:
                                    sppval = str(row[0])
                                    spp.write("WARNING: " + sppval + " is not on the biological species list.\n")
                        # Get counts of Proposed Biological Treatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "BCP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "RLSITE_TX", "CAUTION_TX", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "CO_CM_TX", "DIR_CM_TX"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        pbioloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if str(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pbiosppfm = arcpy.FieldMappings()
                        pbiosppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", pbiosppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "BCP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "RLSITE_TX", "CAUTION_TX", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "CO_CM_TX", "DIR_CM_TX", "SCNTFC_CD"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        pbiospp += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_bioagct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_bioagct", "BIO_SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_bioagct", fc + "_bioagct" + str(fldct), "\"" + field.name + "\" IS NOT NULL")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "BIO_SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")                                
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "SPC_USE_QY", "!SPC_USE_QY" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "HSTMATL_NM", "!HSTMATL_NM" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "PRMT_DT", "!PRMT_DT" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "PRMTREQ_FL", "!PRMTREQ_FL" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "LFCYCLE_NM", "!LFCYCLE_NM" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "CLLCNTY_NM", "!CLLCNTY_NM" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "CLSTATE_CD", "!CLSTATE_CD" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_bioagct" + str(fldct), "PRMT_NR", "!PRMT_NR" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        pbioagfm = arcpy.FieldMappings()
                        pbioagfm.addTable(fc + "_bioagct")
                        fclst = arcpy.ListFeatureClasses(fc + "_bioagct*")
                        arcpy.Merge_management(fclst, fc + "_bioagtot", pbioagfm)
                        arcpy.DeleteIdentical_management(fc + "_bioagtot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "BCP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "RLSITE_TX", "CAUTION_TX", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "CO_CM_TX", "DIR_CM_TX", "BIO_SCNTFC_CD", "SPC_USE_QY", "HASTMATL_NM", "PRMT_DT", "PRMTREQ_FL", "LFCYCLE_NM", "CLLCNTY_NM", "CLSTATE_CD", "PRMT_NR"])
                        recct = arcpy.GetCount_management(fc + "_bioagtot").getOutput(0)
                        pbioag += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_biocpct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_biocpct", "COOP_PERS*"):
                            arcpy.Select_analysis(fc + "_biocpct", fc + "_biocpct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_biocpct" + str(fldct), "COOP_PERS", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pbiocpfm = arcpy.FieldMappings()
                        pbiocpfm.addTable(fc + "_biocpct")
                        fclst = arcpy.ListFeatureClasses(fc + "_biocpct*")
                        arcpy.Merge_management(fclst, fc + "_biocptot", pbiocpfm)
                        arcpy.DeleteIdentical_management(fc + "_biocptot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "BCP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "RLSITE_TX", "CAUTION_TX", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "CO_CM_TX", "DIR_CM_TX", "COOP_PERS"])
                        recct = arcpy.GetCount_management(fc + "_biocptot").getOutput(0)
                        pbiocp += int(recct)                       
                        arcpy.CopyFeatures_management(fc, fc + "_bionepact")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_bionepact", "NEPA_NR*"):
                            arcpy.Select_analysis(fc + "_bionepact", fc + "_bionepact" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_bionepact" + str(fldct), "NEPA_NR", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pbionepafm = arcpy.FieldMappings()
                        pbionepafm.addTable(fc + "_bionepact")
                        fclst = arcpy.ListFeatureClasses(fc + "_bionepact*")
                        arcpy.Merge_management(fclst, fc + "_bionepatot", pbionepafm)
                        arcpy.DeleteIdentical_management(fc + "_bionepatot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "BCP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "RLSITE_TX", "CAUTION_TX", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "CO_CM_TX", "DIR_CM_TX", "NEPA_NR"])
                        recct = arcpy.GetCount_management(fc + "_bionepatot").getOutput(0)
                        pbionepa += int(recct)                    
                    # QC for Proposed Chemical Treatment data
                    if "Chemical" in fc:
                        arcpy.Select_analysis(fc, fc + "_ag", "\"TRADE_NM\" IS NULL OR \"TRADE_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_ag").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":TRADE_NM is missing values. TRADE_NM is a required field.\n")
                        # Get counts of Proposed Chemical Treatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        pchemloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pchemsppfm = arcpy.FieldMappings()
                        pchemsppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", pchemsppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "SCNTFC_CD"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        pchemspp += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_chemagct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_chemagct", "TRADE_NM*"):
                            arcpy.Select_analysis(fc + "_chemagct", fc + "_chemagct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_chemagct" + str(fldct), "TRADE_NM", "!" + field.name + "!", "PYTHON_9.3")                                
                                arcpy.CalculateField_management(fc + "_chemagct" + str(fldct), "MNFCTR_NM", "!MNFCTR_NM" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_chemagct" + str(fldct), "APP_RT_TX", "!APP_RT_TX" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_chemagct" + str(fldct), "APP_AMT_LOW", "!APP_AMT_LOW" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_chemagct" + str(fldct), "APP_AMT_HIGH", "!APP_AMT_HIGH" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        pchemagfm = arcpy.FieldMappings()
                        pchemagfm.addTable(fc + "_chemagct")
                        fclst = arcpy.ListFeatureClasses(fc + "_chemagct*")
                        arcpy.Merge_management(fclst, fc + "_chemagtot", pchemagfm)
                        arcpy.DeleteIdentical_management(fc + "_chemagtot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "TRADE_NM", "MNFCTR_NM", "APP_RT_TX", "APP_AMT_LOW", "APP_AMT_HIGH"])
                        recct = arcpy.GetCount_management(fc + "_chemagtot").getOutput(0)
                        pchemag += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_chemcpct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_chemcpct", "COOP_PERS*"):
                            arcpy.Select_analysis(fc + "_chemcpct", fc + "_chemcpct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_chemcpct" + str(fldct), "COOP_PERS", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pchemcpfm = arcpy.FieldMappings()
                        pchemcpfm.addTable(fc + "_chemcpct")
                        fclst = arcpy.ListFeatureClasses(fc + "_chemcpct*")
                        arcpy.Merge_management(fclst, fc + "_chemcptot", pchemcpfm)
                        arcpy.DeleteIdentical_management(fc + "_chemcptot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "COOP_PERS"])
                        recct = arcpy.GetCount_management(fc + "_chemcptot").getOutput(0)
                        pchemcp += int(recct)                       
                        arcpy.CopyFeatures_management(fc, fc + "_chemnepact")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_chemnepact", "NEPA_NR*"):
                            arcpy.Select_analysis(fc + "_chemnepact", fc + "_chemnepact" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_chemnepact" + str(fldct), "NEPA_NR", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pchemnepafm = arcpy.FieldMappings()
                        pchemnepafm.addTable(fc + "_chemnepact")
                        fclst = arcpy.ListFeatureClasses(fc + "_chemnepact*")
                        arcpy.Merge_management(fclst, fc + "_chemnepatot", pchemnepafm)
                        arcpy.DeleteIdentical_management(fc + "_chemnepatot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "PUP_NR", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "NEPA_NR"])
                        recct = arcpy.GetCount_management(fc + "_chemnepatot").getOutput(0)
                        pchemnepa += int(recct)
                    # Get counts of Proposed Other Treatment data
                    if "Other" in fc:
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "CO_CM_TX", "DIR_CM_TX"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        pothloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pothsppfm = arcpy.FieldMappings()
                        pothsppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", pothsppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "CO_CM_TX", "DIR_CM_TX", "SCNTFC_CD"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        pothspp += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_othcpct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_othcpct", "COOP_PERS*"):
                            arcpy.Select_analysis(fc + "_othcpct", fc + "_othcpct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_othcpct" + str(fldct), "COOP_PERS", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pothcpfm = arcpy.FieldMappings()
                        pothcpfm.addTable(fc + "_othcpct")
                        fclst = arcpy.ListFeatureClasses(fc + "_othcpct*")
                        arcpy.Merge_management(fclst, fc + "_othcptot", pothcpfm)
                        arcpy.DeleteIdentical_management(fc + "_othcptot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "CO_CM_TX", "DIR_CM_TX", "COOP_PERS"])
                        recct = arcpy.GetCount_management(fc + "_othcptot").getOutput(0)
                        pothcp += int(recct)                       
                        arcpy.CopyFeatures_management(fc, fc + "_othnepact")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_othnepact", "NEPA_NR*"):
                            arcpy.Select_analysis(fc + "_othnepact", fc + "_othnepact" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_othnepact" + str(fldct), "NEPA_NR", "!" + field.name + "!", "PYTHON_9.3")
                            fldct += 1
                        pothnepafm = arcpy.FieldMappings()
                        pothnepafm.addTable(fc + "_othnepact")
                        fclst = arcpy.ListFeatureClasses(fc + "_othnepact*")
                        arcpy.Merge_management(fclst, fc + "_othnepatot", pchemnepafm)
                        arcpy.DeleteIdentical_management(fc + "_othnepatot", ["SHAPE", "APPL_YR_QY", "PRP_TX", "PR_ACRE_QY", "NR_APPL", "LOC_NM", "TIMEFRAME", "PRP_DATE", "NONTRGT_TX", "IPM_TX", "DPS_TX", "ORIG_LE", "REVIEWER_LE", "REV_APPCD", "PARK_LE", "PARK_APPCD", "ST_COORD_LE", "COOR_APPCD", "ST_DIR_LE", "DIR_APPCD", "ORIG_CM_TX", "REV_CM_TX", "PARK_CM_TX", "CO_CM_TX", "DIR_CM_TX", "NEPA_NR"])
                        recct = arcpy.GetCount_management(fc + "_othnepatot").getOutput(0)
                        pothnepa += int(recct)
                # QC for all Treatment data
                if "Component" in fc:
                    arcpy.Select_analysis(fc, fc + "_tbdtnull", "\"TRT_BEG_DT\" IS NULL")
                    recct = arcpy.GetCount_management(fc + "_tbdtnull").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":TRT_BEG_DT is missing values. TRT_BEG_DT is a required field.\n")
                    arcpy.Select_analysis(fc, fc + "_tbdtnotnull", "\"TRT_BEG_DT\" IS NOT NULL")
                    arcpy.AddField_management(fc + "_tbdtnotnull", "tempdt", "DATE")
                    arcpy.CalculateField_management(fc + "_tbdtnotnull", "tempdt", "datetime.datetime.now()", "PYTHON_9.3")
                    arcpy.Select_analysis(fc + "_tbdtnotnull", fc + "_tbdtfut", "\"TRT_BEG_DT\" > \"tempdt\"")
                    recct = arcpy.GetCount_management(fc + "_tbdtfut").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":TRT_BEG_DT contains future dates.\n")
                    arcpy.AddField_management(fc + "_tbdtnotnull", "dtstatus", "TEXT", "", "", 30)
                    arcpy.CalculateField_management(fc + "_tbdtnotnull", "dtstatus", "str(!TRT_BEG_DT!)", "PYTHON_9.3")
                    arcpy.Select_analysis(fc + "_tbdtnotnull", fc + "tbdttm", "\"dtstatus\" NOT LIKE '%-%' AND \"dtstatus\" NOT LIKE '%/%'")
                    recct = arcpy.GetCount_management(fc + "tbdttm").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":TRT_BEG_DT contains invalid values.\n")
                    arcpy.Select_analysis(fc + "_tbdtnotnull", fc + "_endbef", "\"TRT_BEG_DT\" > \"TRT_END_DT\" AND \"TRT_END_DT\" IS NOT NULL")
                    recct = arcpy.GetCount_management(fc + "_endbef").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: "  + fc + ":TRT_BEG_DT occurs after TRT_END_DT.\n")
                    for field in arcpy.ListFields(fc, "EST_CVR_RT*"):
                        fldct = field.name[10:]
                        arcpy.Select_analysis(fc, fc + "_cvrnull" + str(fldct), "\"" + field.name + "\" IS NULL AND \"SCNTFC_CD" + str(fldct) + "\" IS NOT NULL")
                        recct = arcpy.GetCount_management(fc + "_cvrnull" + str(fldct)).getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":" + field.name + " is missing values. " + field.name + " is a required field when a species is reported.\n")
                    # QC for all Biological Treatment data
                    if "Biological" in fc:
                        for field in arcpy.ListFields(fc, "EST_CVR_RT*"):
                            fldct = field.name[10:]
                            arcpy.Select_analysis(fc, fc + "_cvrzero" + str(fldct), "\"" + field.name + "\" = 0 AND \"SCNTFC_CD\" IS NOT NULL")
                            recct = arcpy.GetCount_management(fc + "_cvrzero" + str(fldct)).getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " contains 0 values. A value greater than zero is required when a species is reported for biological treatment.\n")
                        arcpy.Select_analysis(fc, fc + "_bag", "\"BIO_SCNTFC_CD\" IS NULL OR \"BIO_SCNTFC_CD\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_bag").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":BIO_SCNTFC_CD is missing values. BIO_SCNTFC_CD is a required field.\n")
                        arcpy.Select_analysis(fc, fc + "_bagnotnull", "\"BIO_SCNTFC_CD\" IS NOT NULL AND \"BIO_SCNTFC_CD\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")                            
                        arcpy.JoinField_management(fc + "_bagnotnull", "BIO_SCNTFC_CD", InAdmin + "\\NISIMS.gdb\\domApprovBioControl", "SPPCD")
                        arcpy.Select_analysis(fc + "_bagnotnull", fc + "_bspp", "\"SPPCD\" IS NULL AND \"BIO_SCNTFC_CD\" IS NOT NULL")
                        arcpy.DeleteField_management(fc + "_bagnotnull", "SPPCD")
                        recct = arcpy.GetCount_management(fc + "_bspp").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_bspp", ["BIO_SCNTFC_CD"])
                            with arcpy.da.SearchCursor(fc + "_bspp", ["BIO_SCNTFC_CD"]) as cursor:
                                for row in cursor:
                                    sppval = str(row[0])
                                    spp.write("WARNING: " + sppval + " is not on the biological species list.\n")
                        # Get counts of Biological Treatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLYG_NM", "DPC_TX", "BUP_NR", "BIO_SCNTFC_CD", "SPC_USE_QY", "PRTCMTH_TX", "RLSDRCT_TX", "SOURCE", "HSTMATL_NM", "LFCYCLE_NM", "CLLCNTY_NM", "COLLECT_DT", "CLSTATE_CD", "FA_AIR_ME", "WNDMPH_ME", "SL_MOIS_NM", "WNDDRCT_CD", "NOTES"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        bioloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "EST_CVR_RT", "!EST_CVR_RT" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        biosppfm = arcpy.FieldMappings()
                        biosppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", biosppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "BUP_NR", "BIO_SCNTFC_CD", "SPC_USE_QY", "PRTCMTH_TX", "RLSDRCT_TX", "SOURCE", "HSTMATL_NM", "LFCYCLE_NM", "CLLCNTY_NM", "COLLECT_DT", "CLSTATE_CD", "FA_AIR_ME", "WNDMPH_ME", "SL_MOIS_NM", "WNDDRCT_CD", "NOTES", "SCNTFC_CD", "EST_CVR_RT"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        biospp += int(recct)
                    # QC for all Chemical Treatment data
                    if "Chemical" in fc:
                        arcpy.Select_analysis(fc, fc + "_cvrzero", "\"EST_CVR_RT\" = 0 AND \"PTTRN_NM\" <> 'BROADCAST'")
                        recct = arcpy.GetCount_management(fc + "_cvrzero").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":EST_CVR_RT includes 0 values. EST_CVR_RT cannot be zero for chemical treatment data if it was not a broadcast treatment (PTTRN_NM).\n")
                        arcpy.Select_analysis(fc, fc + "_mixuom", "\"MIXUOM_NM\" IS NULL OR \"MIXUOM_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_mixuom").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":MIXUOM_NM is missing values. MIXUOM_NM is a required field.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Chemical_Agent_UOM_Type_Name", InAdmin + "\\NISIMS.gdb\\domCHEMICAL_AGENT_UOM", "CODE", "DESC")
                        arcpy.JoinField_management(fc, "MIXUOM_NM", InAdmin + "\\NISIMS.gdb\\domCHEMICAL_AGENT_UOM", "CODE", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domCHEMICAL_AGENT_UOM")
                        arcpy.Select_analysis(fc, fc + "_mixuomcd", "\"CODE\" IS NULL AND \"MIXUOM_NM\" IS NOT NULL")
                        arcpy.DeleteField_management(fc, "CODE")
                        recct = arcpy.GetCount_management(fc + "_mixuomcd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_mixuomcd", ["MIXUOM_NM"])
                            with arcpy.da.SearchCursor(fc + "_mixuomcd", ["MIXUOM_NM"]) as cursor:
                                for row in cursor:
                                    uomval = str(row[0])
                                    err.write("ERROR: " + uomval + " is not an approved unit of measure for MIXUOM_NM.\n")
                        arcpy.Select_analysis(fc, fc + "_mixvol", "\"MIXVOL_ME\" IS NULL OR \"MIXVOL_ME\" = 0")
                        recct = arcpy.GetCount_management(fc + "_mixvol").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":MIXVOL_ME is missing values. MIXVOL_ME is a required field.\n")
                        arcpy.Select_analysis(fc, fc + "_carrty", "\"CARR_TY_NM\" IS NULL OR \"CARR_TY_NM\" IN (' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_carrty").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":CARR_TY_NM is missing values. CARR_TY_NM is a required field.\n")
                        arcpy.Select_analysis(fc, fc + "_dlvr", "\"DLVR_NM\" IS NULL OR \"DLVR_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_dlvr").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":DLVR_NM is missing values. DLVR_NM is a required field.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Treatment_Delivery_Method_Type_Name", InAdmin + "\\NISIMS.gdb\\domDLVR_NM", "CODE", "DESC")                            
                        arcpy.JoinField_management(fc, "DLVR_NM", InAdmin + "\\NISIMS.gdb\\domDLVR_NM", "CODE", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domDLVR_NM")
                        arcpy.Select_analysis(fc, fc + "_dlvrcd", "\"CODE\" IS NULL AND \"DLVR_NM\" IS NOT NULL")
                        arcpy.DeleteField_management(fc, "CODE")
                        recct = arcpy.GetCount_management(fc + "_dlvrcd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_dlvrcd", ["DLVR_NM"])
                            with arcpy.da.SearchCursor(fc + "_dlvrcd", ["DLVR_NM"]) as cursor:
                                for row in cursor:
                                    dlvrval = str(row[0])
                                    err.write("ERROR: " + dlvrval + " is not an approved delivery method for DLVR_NM.\n")                            
                        arcpy.Select_analysis(fc, fc + "_pttrn", "\"PTTRN_NM\" IS NULL OR \"PTTRN_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_pttrn").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":PTTRN_NM is missing values. PTTRN_NM is a required field.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Treatment_Coverage_Pattern_Type_Name", InAdmin + "\\NISIMS.gdb\\domPTTRN_NM", "CODE", "DESC")                            
                        arcpy.JoinField_management(fc, "PTTRN_NM", InAdmin + "\\NISIMS.gdb\\domPTTRN_NM", "CODE", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domPTTRN_NM")                        
                        arcpy.Select_analysis(fc, fc + "_pttrncd", "\"CODE\" IS NULL AND \"PTTRN_NM\" IS NOT NULL")
                        arcpy.DeleteField_management(fc, "CODE")
                        recct = arcpy.GetCount_management(fc + "_pttrncd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_pttrncd", ["PTTRN_NM"])
                            with arcpy.da.SearchCursor(fc + "_pttrncd", ["PTTRN_NM"]) as cursor:
                                for row in cursor:
                                    ptval = str(row[0])
                                    err.write("ERROR: " + ptval + " is not an approved treatment pattern for PTTRN_NM.\n")
                        arcpy.AddField_management(fc, "tmstatus", "TEXT", "", "", 30)
                        arcpy.CalculateField_management(fc, "tmstatus", "str(!TRT_BEG_TM!)", "PYTHON_9.3")
                        arcpy.Select_analysis(fc, fc + "_time", "\"tmstatus\" IS NULL OR \"tmstatus\" IN ('None', ' ', '') OR \"tmstatus\" NOT LIKE '%:%'")
                        recct = arcpy.GetCount_management(fc + "_time").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":TRT_BEG_TM is missing valid values. TRT_BEG_TM is a required field.\n")
                        arcpy.Select_analysis(fc, fc + "_equom", "(\"EQ_UOM_NM\" IS NULL OR \"EQ_UOM_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND \"EQ_OUT_RT\" IS NOT NULL")
                        recct = arcpy.GetCount_management(fc + "_equom").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":EQ_UOM_NM is missing values. EQ_UOM_NM is required when EQ_OUT_RT is populated.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Equipment_Output_UOM_Type_Name", InAdmin + "\\NISIMS.gdb\\domEQ_OUT_UOM", "CODE", "DESC")                            
                        arcpy.JoinField_management(fc, "EQ_UOM_NM", InAdmin + "\\NISIMS.gdb\\domEQ_OUT_UOM", "CODE", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domEQ_OUT_UOM")                        
                        arcpy.Select_analysis(fc, fc + "_equomcd", "\"CODE\" IS NULL AND \"EQ_UOM_NM\" IS NOT NULL")
                        arcpy.DeleteField_management(fc, "CODE")
                        recct = arcpy.GetCount_management(fc + "_equomcd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_equomcd", ["EQ_UOM_NM"])
                            with arcpy.da.SearchCursor(fc + "_equomcd", ["EQ_UOM_NM"]) as cursor:
                                for row in cursor:
                                    eqval = str(row[0])
                                    err.write("ERROR: " + eqval + " is not an approved unit of measure for EQ_UOM_NM.\n")                            
                        arcpy.Select_analysis(fc, fc + "_ag", "\"TRADE_NM\" IS NULL OR \"TRADE_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_ag").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":TRADE_NM is missing values. TRADE_NM is a required field.\n")
                        for field in arcpy.ListFields(fc, "TRADE_NM*"):
                            if field.name != "TRADE_NM":
                                fldct = str(field.name[8:])
                                arcpy.Select_analysis(fc, fc + "_ag", "(\"" + field.name + "\" IS NULL OR \"" + field.name + "\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND (\"ACTLUSE_QY" + str(fldct) + "\" IS NOT NULL OR \"AGT_APP_RT" + str(fldct) + "\" IS NOT NULL OR \"EPAREGISTRATIONNUMBER" + str(fldct) + "\" IS NOT NULL)")
                                recct = arcpy.GetCount_management(fc + "_ag").getOutput(0)
                                if int(recct) > 0:
                                    err.write("ERROR: " + fc + ":" + field.name + " is missing values. TRADE_NM is required if EPAREGISTRATIONNUMBER, ACTLUSE_QY, or AGT_APP_RT are populated.\n")
                        for field in arcpy.ListFields(fc, "EPAREGISTRATIONNUMBER*"):
                            fldct = str(field.name[21:])
                            arcpy.Select_analysis(fc, fc + "_epa", "(\"" + field.name + "\" IS NULL OR \"" + field.name + "\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND \"TRADE_NM" + str(fldct) + "\" IS NOT NULL")
                            recct = arcpy.GetCount_management(fc + "_epa").getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " is missing values. EPAREGISTRATIONNUMBER is required if TRADE_NM is populated.\n")
                        for field in arcpy.ListFields(fc, "ACTLUSE_QY*"):
                            fldct = str(field.name[10:])
                            arcpy.Select_analysis(fc, fc + "_agqty", "\"" + field.name + "\" IS NULL AND (\"AGT_APP_RT" + str(fldct) + "\" IS NULL AND \"TRADE_NM" + str(fldct) + "\" IS NOT NULL)")
                            recct = arcpy.GetCount_management(fc + "_agqty").getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " or AGT_APP_RT" + str(fldct) + " are missing values. Either ACTLUSE_QY or AGT_APP_RT are required if TRADE_NM is populated.\n")
                        for field in arcpy.ListFields(fc, "APP_UOM_NM*"):
                            fldct = str(field.name[10:])
                            arcpy.Select_analysis(fc, fc + "_agrtuom", "(\"" + field.name + "\" IS NULL OR \"" + field.name + "\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND \"AGT_APP_RT" + str(fldct) + "\" IS NOT NULL")
                            recct = arcpy.GetCount_management(fc + "_agrtuom").getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " is missing values. APP_UOM_NM must be populated if AGT_APP_RT is populated.\n")
                            arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Application_Rate_UOM_Type_Name", InAdmin + "\\NISIMS.gdb\\domAPP_RT_UOM", "CODE", "DESC")                                
                            arcpy.JoinField_management(fc, field.name, InAdmin + "\\NISIMS.gdb\\domAPP_RT_UOM", "CODE", "CODE")
                            arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domAPP_RT_UOM")
                            arcpy.Select_analysis(fc, fc + "_rtcd", "\"CODE\" IS NULL AND \"" + field.name + "\" IS NOT NULL")
                            arcpy.DeleteField_management(fc, "CODE")
                            recct = arcpy.GetCount_management(fc + "_rtcd").getOutput(0)
                            if int(recct) > 0:
                                arcpy.DeleteIdentical_management(fc + "_rtcd", [field.name])
                                with arcpy.da.SearchCursor(fc + "_rtcd", [field.name]) as cursor:
                                    for row in cursor:
                                        rtval = str(row[0])
                                        err.write("ERROR: " + rtval + " is not an approved unit of measure for " + field.name + ".\n")
                        for field in arcpy.ListFields(fc, "AGT_UOM_NM*"):
                            fldct = str(field.name[10:])
                            arcpy.Select_analysis(fc, fc + "_agqtyuom", "(\"" + field.name + "\" IS NULL OR \"" + field.name + "\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND \"ACTLUSE_QY" + str(fldct) + "\" IS NOT NULL")
                            recct = arcpy.GetCount_management(fc + "_agqtyuom").getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " is missing values. AGT_UOM_NM must be populated if ACTLUSE_QY is populated.\n")
                            arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Chemical_Agent_UOM_Type_Name", InAdmin + "\\NISIMS.gdb\\domCHEMICAL_AGENT_NM", "CODE", "DESC")                                
                            arcpy.JoinField_management(fc, field.name, InAdmin + "\\NISIMS.gdb\\domCHEMICAL_AGENT_NM", "CODE", "CODE")
                            arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domCHEMICAL_AGENT_NM")
                            arcpy.Select_analysis(fc, fc + "_qtycd", "\"CODE\" IS NULL AND \"" + field.name + "\" IS NOT NULL")
                            arcpy.DeleteField_management(fc, "CODE")
                            recct = arcpy.GetCount_management(fc + "_qtycd").getOutput(0)
                            if int(recct) > 0:
                                arcpy.DeleteIdentical_management(fc + "_qtycd", [field.name])
                                with arcpy.da.SearchCursor(fc + "_qtycd", [field.name]) as cursor:
                                    for row in cursor:
                                        qtyval = str(row[0])
                                        err.write("ERROR: " + qtyval + " is not an approved unit of measure for " + field.name + ".\n")                                    
                        for field in arcpy.ListFields(fc, "ADJ_TRADE_NM*"):
                            fldct = str(field.name[12:])
                            arcpy.Select_analysis(fc, fc + "_adj", "(\"" + field.name + "\" IS NULL OR \"" + field.name + "\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND (\"ADJ_ACTLUSE_QTY" + str(fldct) + "\" IS NOT NULL OR \"ADJ_AGT_APP_RT" + str(fldct) + "\" IS NOT NULL)")
                            recct = arcpy.GetCount_management(fc + "_adj").getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " is missing values. ADJ_TRADE_NM is required if ADJ_ACTLUSE_QY or ADJ_AGT_APP_RT are populated.\n")
                        for field in arcpy.ListFields(fc, "ADJ_APP_UOM_NM*"):
                            fldct = str(field.name[14:])
                            arcpy.Select_analysis(fc, fc + "_adjrtuom", "(\"" + field.name + "\" IS NULL OR \"" + field.name + "\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND \"ADJ_AGT_APP_RT" + str(fldct) + "\" IS NOT NULL")
                            recct = arcpy.GetCount_management(fc + "_adjrtuom").getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " is missing values. ADJ_APP_UOM_NM must be populated if ADJ_AGT_APP_RT is populated.\n")
                            arcpy.management.DomainToTable(InAdmin + "\\NISIMS.gdb", "Application_Rate_UOM_Type_Name", InAdmin + "\\NISIMS.gdb\\domAPP_RT_UOM", "CODE", "DESC")                                  
                            arcpy.JoinField_management(fc, field.name, InAdmin + "\\NISIMS.gdb\\domAPP_RT_UOM", "CODE", "CODE")
                            arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domAPP_RT_UOM")
                            arcpy.Select_analysis(fc, fc + "_adjrtcd", "\"CODE\" IS NULL AND \"" + field.name + "\" IS NOT NULL")
                            arcpy.DeleteField_management(fc, "CODE")
                            recct = arcpy.GetCount_management(fc + "_adjrtcd").getOutput(0)
                            if int(recct) > 0:
                                arcpy.DeleteIdentical_management(fc + "_adjrtcd", [field.name])
                                with arcpy.da.SearchCursor(fc + "_adjrtcd", [field.name]) as cursor:
                                    for row in cursor:
                                        adjrtval = str(row[0])
                                        err.write("ERROR: " + adjrtval + " is not an approved unit of measure for " + field.name + ".\n")
                        for field in arcpy.ListFields(fc, "ADJ_AGT_UOM_NM*"):
                            fldct = str(field.name[14:])
                            arcpy.Select_analysis(fc, fc + "_adjqtyuom", "(\"" + field.name + "\" IS NULL OR \"" + field.name + "\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND \"ADJ_ACTLUSE_QTY" + str(fldct) + "\" IS NOT NULL")
                            recct = arcpy.GetCount_management(fc + "_adjqtyuom").getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " is missing values. ADJ_AGT_UOM_NM must be populated if ADJ_ACTLUSE_QTY is populated.\n")
                            arcpy.management.DomainToTable(InAdmin + "\\NISIMS.gdb", "Adjuvant_UOM_Type_Name", InAdmin + "\\NISIMS.gdb\\domADJUVANT_AGENT_NM", "CODE", "DESC")                                
                            arcpy.JoinField_management(fc, field.name, InAdmin + "\\NISIMS.gdb\\domADJUVANT_AGENT_NM", "CODE", "CODE")
                            arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domADJUVANT_AGENT_NM")
                            arcpy.Select_analysis(fc, fc + "_adjqtycd", "\"CODE\" IS NULL AND \"" + field.name + "\" IS NOT NULL")
                            arcpy.DeleteField_management(fc, "CODE")
                            recct = arcpy.GetCount_management(fc + "_adjqtycd").getOutput(0)
                            if int(recct) > 0:
                                arcpy.DeleteIdentical_management(fc + "_adjqtycd", [field.name])
                                with arcpy.da.SearchCursor(fc + "_adjqtycd", [field.name]) as cursor:
                                    for row in cursor:
                                        adjqtyval = str(row[0])
                                        err.write("ERROR: " + adjqtyval + " is not an approved unit of measure for " + field.name + ".\n")                                
                        # Get counts of Chemical Treatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "TRT_BEG_TM", "TRT_END_TM", "PHNLGY_NM", "DPC_TX", "MIXUOM_NM", "MIXVOL_ME", "CARR_TY_NM", "RLSDRCT_TX", "PUP_NR", "DLVR_NM", "PTTRN_NM", "WTRDIST_TX", "EQ_OUT_RT", "EQ_UOM_NM", "EQ_TY_NM", "FA_AIR_ME", "HUMID_RT", "WNDMPH_ME", "SL_MOIS_ME", "PRECIP_NM", "WNDDRCT_CD", "TRADE_NM", "AGT_APP_RT", "ACTLUSE_QY", "AGT_UOM_NM", "APP_UOM_NM", "TRADE_NM2", "AGT_APP_RT2", "ACTLUSE_QY2", "AGT_UOM_NM2", "APP_UOM_NM2", "ADJ_TRADE_NM", "ADJ_TRADE_NM2", "AGT_APP_RT", "AGT_APP_RT2", "ADJ_AGT_APP_RT", "ADJ_APP_UOM_NM", "ADJ_AGT_APP_RT2", "ADJ_APP_UOM_NM2", "NOTES"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        chemloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):                        
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "EST_CVR_RT", "!EST_CVR_RT" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        chemsppfm = arcpy.FieldMappings()
                        chemsppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", chemsppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "TRT_BEG_TM", "TRT_END_TM", "PHNLGY_NM", "DPC_TX", "MIXUOM_NM", "MIXVOL_ME", "CARR_TY_NM", "RLSDRCT_TX", "PUP_NR", "DLVR_NM", "PTTRN_NM", "WTRDIST_TX", "EQ_OUT_RT", "EQ_UOM_NM", "EQ_TY_NM", "FA_AIR_ME", "HUMID_RT", "WNDMPH_ME", "SL_MOIS_ME", "PRECIP_NM", "WNDDRCT_CD", "TRADE_NM", "APP_UOM_NM", "TRADE_NM2", "APP_UOM_NM2", "ADJ_TRADE_NM", "ADJ_TRADE_NM2", "AGT_APP_RT", "AGT_APP_RT2", "ADJ_AGT_APP_RT", "ADJ_APP_UOM_NM", "ADJ_AGT_APP_RT2", "ADJ_APP_UOM_NM2", "NOTES", "SCNTFC_CD", "EST_CVR_RT"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        chemspp += int(recct)                                
                        arcpy.CopyFeatures_management(fc, fc + "_agct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_agct", "TRADE_NM*"):                        
                            arcpy.Select_analysis(fc + "_agct", fc + "_agct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_agct" + str(fldct), "TRADE_NM", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_agct" + str(fldct), "AGT_APP_RT", "!AGT_APP_RT" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_agct" + str(fldct), "APP_UOM_NM", "!APP_UOM_NM" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_agct" + str(fldct), "ACTLUSE_QY", "!ACTLUSE_QY" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_agct" + str(fldct), "AGT_UOM_NM", "!AGT_UOM_NM" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_agct" + str(fldct), "MNFCTR_NM", "!MNFCTR_NM" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_agct" + str(fldct), "EPAREGISTRATIONNUMBER", "!EPAREGISTRATIONNUMBER" + str(fldct) + "!", "PYTHON_9.3")                                 
                            fldct += 1
                        chemagfm = arcpy.FieldMappings()
                        chemagfm.addTable(fc + "_agct")
                        fclst = arcpy.ListFeatureClasses(fc + "_agct*")
                        arcpy.Merge_management(fclst, fc + "_agtot", chemagfm)
                        arcpy.DeleteIdentical_management(fc + "_agtot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "TRT_BEG_TM", "TRT_END_TM", "PHNLGY_NM", "DPC_TX", "MIXUOM_NM", "MIXVOL_ME", "CARR_TY_NM", "RLSDRCT_TX", "PUP_NR", "DLVR_NM", "PTTRN_NM", "WTRDIST_TX", "EQ_OUT_RT", "EQ_UOM_NM", "EQ_TY_NM", "FA_AIR_ME", "HUMID_RT", "WNDMPH_ME", "SL_MOIS_ME", "PRECIP_NM", "WNDDRCT_CD", "TRADE_NM", "APP_UOM_NM", "TRADE_NM2", "APP_UOM_NM2", "ADJ_TRADE_NM", "ADJ_TRADE_NM2", "AGT_APP_RT", "AGT_APP_RT2", "ADJ_AGT_APP_RT", "ADJ_APP_UOM_NM", "ADJ_AGT_APP_RT2", "ADJ_APP_UOM_NM2", "NOTES", "TRADE_NM", "AGT_APP_RT", "APP_UOM_NM", "ATCLUSE_QY", "AGT_UOM_NM", "MNFCTR_NM", "EPAREGISTRATIONNUMBER"])
                        recct = arcpy.GetCount_management(fc + "_agtot").getOutput(0)
                        chemag += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_adjct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_adjct", "ADJ_TRADE_NM*"):                        
                            arcpy.Select_analysis(fc + "_adjct", fc + "_seladjct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_seladjct" + str(fldct), "ADJ_TRADE_NM", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_seladjct" + str(fldct), "ADJ_AGT_APP_RT", "!ADJ_AGT_APP_RT" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_seladjct" + str(fldct), "ADJ_APP_UOM_NM", "!ADJ_APP_UOM_NM" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_seladjct" + str(fldct), "ADJ_ACTLUSE_QTY", "!ADJ_ACTLUSE_QTY" + str(fldct) + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_seladjct" + str(fldct), "ADJ_AGT_UOM_NM", "!ADJ_AGT_UOM_NM" + str(fldct) + "!", "PYTHON_9.3")                                
                            fldct += 1
                        chemadjfm = arcpy.FieldMappings()
                        chemadjfm.addTable(fc + "_adjct")
                        fclst = arcpy.ListFeatureClasses(fc + "_seladjct*")
                        arcpy.Merge_management(fclst, fc + "_adjtot", chemadjfm)
                        arcpy.DeleteIdentical_management(fc + "_adjtot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "TRT_BEG_TM", "TRT_END_TM", "PHNLGY_NM", "DPC_TX", "MIXUOM_NM", "MIXVOL_ME", "CARR_TY_NM", "RLSDRCT_TX", "PUP_NR", "DLVR_NM", "PTTRN_NM", "WTRDIST_TX", "EQ_OUT_RT", "EQ_UOM_NM", "EQ_TY_NM", "FA_AIR_ME", "HUMID_RT", "WNDMPH_ME", "SL_MOIS_ME", "PRECIP_NM", "WNDDRCT_CD", "TRADE_NM", "APP_UOM_NM", "TRADE_NM2", "APP_UOM_NM2", "ADJ_TRADE_NM", "ADJ_TRADE_NM2", "AGT_APP_RT", "AGT_APP_RT2", "ADJ_AGT_APP_RT", "ADJ_APP_UOM_NM", "ADJ_AGT_APP_RT2", "ADJ_APP_UOM_NM2", "NOTES", "TRADE_NM", "AGT_APP_RT", "APP_UOM_NM", "ATCLUSE_QY", "AGT_UOM_NM", "TRADE_NM2", "AGT_APP_RT2", "APP_UOM_NM2", "ATCLUSE_QY2", "AGT_UOM_NM2", "ADJ_TRADE_NM", "ADJ_AGT_APP_RT", "ADJ_APP_UOM_NM", "ADJ_ACTLUSE_QTY", "ADJ_AGT_UOM_NM"])
                        recct = arcpy.GetCount_management(fc + "_adjtot").getOutput(0)
                        chemadj += int(recct)                    
                    # QC for all Fire Treatment data
                    if "Fire" in fc:
                        arcpy.Select_analysis(fc, fc + "_int", "\"INTNSTY_NM\" IS NULL OR \"INTNSTY_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_int").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":INTNSTY_NM is missing values. INTNSTY_NM is a required field.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Burn_Intensity_Type_Name", InAdmin + "\\NISIMS.gdb\\domINTNSTY", "CODE", "DESC")
                        arcpy.Select_analysis(fc, fc + "_intnotnull", "\"INTNSTY_NM\" IS NOT NULL AND \"INTNSTY_NM\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        arcpy.JoinField_management(fc + "_intnotnull", "INTNSTY_NM", InAdmin + "\\NISIMS.gdb\\domINTNSTY", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domINTNSTY")
                        arcpy.Select_analysis(fc + "_intnotnull", fc + "_intcd", "\"CODE\" IS NULL AND \"INTNSTY_NM\" IS NOT NULL")
                        arcpy.DeleteField_management(fc + "_intnotnull", "CODE")
                        recct = arcpy.GetCount_management(fc + "_intcd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_intcd", ["INTNSTY_NM"])
                            with arcpy.da.SearchCursor(fc + "_intcd", ["INTNSTY_NM"]) as cursor:
                                for row in cursor:
                                    intval = str(row[0])
                                    err.write("ERROR: " + intval + " is not an approved value for INTNSTY_NM.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Fuel_Model_Text", InAdmin + "\\NISIMS.gdb\\domFUELMDL", "CODE", "DESC")                                    
                        arcpy.JoinField_management(fc, "FUELMDL_TX", InAdmin + "\\NISIMS.gdb\\domFUELMDL", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domFUELMDL")                        
                        arcpy.Select_analysis(fc, fc + "_fuelcd", "\"CODE\" IS NULL AND \"FUELMDL_TX\" IS NOT NULL")
                        arcpy.DeleteField_management(fc, "CODE")
                        recct = arcpy.GetCount_management(fc + "_fuelcd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_fuelcd", ["FUELMDL_TX"])
                            with arcpy.da.SearchCursor(fc + "_fuelcd", ["FUELMDL_TX"]) as cursor:
                                for row in cursor:
                                    fuelval = str(row[0])
                                    err.write("ERROR: " + fuelval + " is not an approved value for FUELMDL_TX.\n")
                        # Get counts of Fire Treatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "INTNSTY_NM", "FUELMDL_TX", "NOTES"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        firloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "EST_CVR_RT", "!EST_CVR_RT" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        firsppfm = arcpy.FieldMappings()
                        firsppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", firsppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "INTNSTY_NM", "FUELMDL_TX", "NOTES", "SCNTFC_CD", "EST_CVR_RT"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        firspp += int(recct)
                    # QC for all Manual Treatment data
                    if "Manual" in fc:
                        for field in arcpy.ListFields(fc, "EST_CVR_RT*"):
                            fldct = field.name[10:]
                            arcpy.Select_analysis(fc, fc + "_cvrzero" + str(fldct), "\"" + field.name + "\" = 0 AND \"SCNTFC_CD\" IS NOT NULL")
                            recct = arcpy.GetCount_management(fc + "_cvrzero" + str(fldct)).getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " contains 0 values. A value greater than zero is required when a species is reported for manual treatment.\n")                                              
                        arcpy.Select_analysis(fc, fc + "_man", "\"MANL_CL_NM\" IS NULL OR \"MANL_CL_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_man").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":MANL_CL_NM is missing values. MANL_CL_NM is a required field.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Manual_Component_Class_Name", InAdmin + "\\NISIMS.gdb\\domMANLCL", "CODE", "DESC")                            
                        arcpy.Select_analysis(fc, fc + "_mannotnull", "\"MANL_CL_NM\" IS NOT NULL AND \"MANL_CL_NM\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        arcpy.JoinField_management(fc + "_mannotnull", "MANL_CL_NM", InAdmin + "\\NISIMS.gdb\\domMANLCL", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domMANLCL")
                        arcpy.Select_analysis(fc + "_mannotnull", fc + "_mancd", "\"CODE\" IS NULL AND \"MANL_CL_NM\" IS NOT NULL")
                        arcpy.DeleteField_management(fc + "_mannotnull", "CODE")
                        recct = arcpy.GetCount_management(fc + "_mancd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_mancd", ["MANL_CL_NM"])
                            with arcpy.da.SearchCursor(fc + "_mancd", ["MANL_CL_NM"]) as cursor:
                                for row in cursor:
                                    manval = str(row[0])
                                    err.write("ERROR: " + manval + " is not an approved value for MANL_CL_NM.\n")
                        # Get counts of Manual Treatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "MANL_CL_NM", "NOTES"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        manloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "EST_CVR_RT", "!EST_CVR_RT" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        mansppfm = arcpy.FieldMappings()
                        mansppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", mansppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "MANL_CL_NM", "NOTES", "SCNTFC_CD", "EST_CVR_RT"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        manspp += int(recct)
                    # QC for all Mechanical Treatment data
                    if "Mechanical" in fc:
                        for field in arcpy.ListFields(fc, "EST_CVR_RT*"):
                            fldct = field.name[10:]
                            arcpy.Select_analysis(fc, fc + "_cvrzero" + str(fldct), "\"" + field.name + "\" = 0 AND \"SCNTFC_CD\" IS NOT NULL")
                            recct = arcpy.GetCount_management(fc + "_cvrzero" + str(fldct)).getOutput(0)
                            if int(recct) > 0:
                                err.write("ERROR: " + fc + ":" + field.name + " contains 0 values. A value greater than zero is required when a species is reported for manual treatment.\n")                                              
                        arcpy.Select_analysis(fc, fc + "_mech", "\"MECH_CL_NM\" IS NULL OR \"MECH_CL_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_mech").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":MECH_CL_NM is missing values. MECH_CL_NM is a required field.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Mechanical_Component_Class_Name", InAdmin + "\\NISIMS.gdb\\domMECHCL", "CODE", "DESC")                            
                        arcpy.Select_analysis(fc, fc + "_mechnotnull", "\"MECH_CL_NM\" IS NOT NULL AND \"MECH_CL_NM\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        arcpy.JoinField_management(fc + "_mechnotnull", "MECH_CL_NM", InAdmin + "\\NISIMS.gdb\\domMECHCL", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domMECHCL")
                        arcpy.Select_analysis(fc + "_mechnotnull", fc + "_mechcd", "\"CODE\" IS NULL AND \"MECH_CL_NM\" IS NOT NULL")
                        arcpy.DeleteField_management(fc + "_mechnotnull", "CODE")
                        recct = arcpy.GetCount_management(fc + "_mechcd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_mechcd", ["MECH_CL_NM"])
                            with arcpy.da.SearchCursor(fc + "_mechcd", ["MECH_CL_NM"]) as cursor:
                                for row in cursor:
                                    mechval = str(row[0])
                                    err.write("ERROR: " + mechval + " is not an approved value for MECH_CL_NM.\n")
                        # Get counts of Mechanical Treatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "MECH_CL_NM", "NOTES"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        mechloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "EST_CVR_RT", "!EST_CVR_RT" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        mechsppfm = arcpy.FieldMappings()
                        mechsppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", mechsppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "MECH_CL_NM", "NOTES", "SCNTFC_CD", "EST_CVR_RT"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        mechspp += int(recct)
                    # QC for all Restoration Treatment data
                    if "Restoration" in fc:
                        arcpy.Select_analysis(fc, fc + "_rest", "\"REST_CL_NM\" IS NULL OR \"REST_CL_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_rest").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":REST_CL_NM is missing values. REST_CL_NM is a required field.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Restoration_Component_Class_Name", InAdmin + "\\NISIMS.gdb\\domRESTCL", "CODE", "DESC")                            
                        fldct = 1     
                        for field in arcpy.ListFields(fc, "REST_CL_NM*"):
                            arcpy.Select_analysis(fc, fc + "_restlst" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            recct = arcpy.GetCount_management(fc + "_restlst" + str(fldct)).getOutput(0)
                            if int(recct) > 0:
                                arcpy.JoinField_management(fc + "_restlst" + str(fldct), field.name, InAdmin + "\\NISIMS.gdb\\domRESTCL", "CODE")
                                arcpy.Select_analysis(fc + "_restlst" + str(fldct), fc + "_badrest" + str(fldct), "\"CODE\" IS NULL AND \"" + field.name + "\" IS NOT NULL")
                                if int(fldct) > 1:
                                    arcpy.CalculateField_management(fc + "_badrest" + str(fldct), "REST_CL_NM", "!" + field.name + "!", "PYTHON_9.3")
                                fldct += 1                    
                        resmap = arcpy.FieldMappings()
                        resmap.addTable(fc)
                        fclst = arcpy.ListFeatureClasses(fc + "_badrest*")
                        arcpy.Merge_management(fclst, fc + "_restall", resmap)
                        recct = arcpy.GetCount_management(fc + "_restall").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_resall", ["REST_CL_NM"])
                            with arcpy.da.SearchCursor(fc + "_resall", ["REST_CL_NM"]) as cursor:
                                for row in cursor:
                                    resval = str(row[0])
                                    err.write("ERROR: " + resval + " is not an approved value for REST_CL_NM.\n")
                        # Get counts of RestorationTreatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "REST_CL_NM", "NOTES"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        resloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):                        
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "EST_CVR_RT", "!EST_CVR_RT" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        chemsppfm = arcpy.FieldMappings()
                        chemsppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", chemsppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "REST_CL_NM", "NOTES", "SCNTFC_CD", "EST_CVR_RT"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        resspp += int(recct)                                
                        arcpy.CopyFeatures_management(fc, fc + "_actct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_actct", "REST_CL_NM*"):                        
                            arcpy.Select_analysis(fc + "_actct", fc + "_actct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_actct" + str(fldct), "REST_CL_NM", "!" + field.name + "!", "PYTHON_9.3")                               
                            fldct += 1
                        restagfm = arcpy.FieldMappings()
                        restagfm.addTable(fc + "_actct")
                        fclst = arcpy.ListFeatureClasses(fc + "_actct*")
                        arcpy.Merge_management(fclst, fc + "_acttot", restagfm)
                        arcpy.DeleteIdentical_management(fc + "_acttot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "REST_CL_NM"])
                        recct = arcpy.GetCount_management(fc + "_acttot").getOutput(0)
                        resact += int(recct)
                    # QC for all Revegetation Treatment data
                    if "Revegetation" in fc:
                        arcpy.Select_analysis(fc, fc + "_stck", "\"STOCK_ME\" IS NULL")
                        recct = arcpy.GetCount_management(fc + "_stck").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":STOCK_ME is missing values. STOCK_ME is a required field.\n")
                        arcpy.Select_analysis(fc, fc + "_veguom", "\"VEG_UOM_NM\" IS NULL OR \"VEG_UOM_NM\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        recct = arcpy.GetCount_management(fc + "_veguom").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":VEG_UOM_NM is missing values. VEG_UOM_NM is a required field.\n")
                        arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "Unit_Of_Measurement_Type_Name", InAdmin + "\\NISIMS.gdb\\domVEGUOM", "CODE", "DESC")                            
                        arcpy.JoinField_management(fc, "VEG_UOM_NM", InAdmin + "\\NISIMS.gdb\\domVEGUOM", "CODE")
                        arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domVEGUOM")
                        arcpy.Select_analysis(fc, fc + "_uomcd", "\"CODE\" IS NULL AND \"VEG_UOM_NM\" IS NOT NULL")
                        arcpy.DeleteField_management(fc, "CODE")
                        recct = arcpy.GetCount_management(fc + "_uomcd").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_uomcd", ["VEG_UOM_NM"])
                            with arcpy.da.SearchCursor(fc + "_uomcd", ["VEG_UOM_NM"]) as cursor:
                                for row in cursor:
                                    uomval = str(row[0])
                                    err.write("ERROR: " + uomval + " is not an approved unit of measure for VEG_UOM_NM.\n")
                        arcpy.Select_analysis(fc, fc + "_seed", "(\"SEEDLOT_NR\" IS NULL OR \"SEEDLOT_NR\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND (\"RVG_SCNTFC_CD\" IS NULL OR \"RVG_SCNTFC_CD\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na'))")
                        recct = arcpy.GetCount_management(fc + "_seed").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":SEEDLOT_NR and RVG_SCNTFC_CD are missing values. Either SEEDLOT_NR or RVG_SCNTFC_CD are required.\n")
                        arcpy.Select_analysis(fc, fc + "_rsppnotnull", "\"RVG_SCNTFC_CD\" IS NOT NULL AND \"RVG_SCNTFC_CD\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        arcpy.JoinField_management(fc + "_rsppnotnull", "RVG_SCNTFC_CD", InAdmin + "\\NISIMS.gdb\\Reveg_SCNTFC_CD", "SPPCD")
                        arcpy.Select_analysis(fc + "_rsppnotnull", fc + "_rspp", "\"SPPCD\" IS NULL AND \"RVG_SCNTFC_CD\" IS NOT NULL")
                        arcpy.DeleteField_management(fc + "_rsppnotnull", "SPPCD")
                        recct = arcpy.GetCount_management(fc + "_rspp").getOutput(0)
                        if int(recct) > 0:
                            arcpy.DeleteIdentical_management(fc + "_rspp", ["RVG_SCNTFC_CD"])
                            with arcpy.da.SearchCursor(fc + "_rspp", ["RVG_SCNTFC_CD"]) as cursor:
                                for row in cursor:
                                    sppval = str(row[0])
                                    spp.write("WARNING: " + sppval + " is not on the revegetation species list.\n")
                        # Get counts of Revegetation Treatment data
                        arcpy.CopyFeatures_management(fc, fc + "_count")
                        arcpy.DeleteIdentical_management(fc + "_count", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "STOCK_ME", "VEG_UOM_NM", "REVEG_PHNLGY_NM", "SEEDLOT_NR", "RVG_SCNTFC_CD", "NOTES"])
                        recct = arcpy.GetCount_management(fc + "_count").getOutput(0)
                        revloc += int(recct)
                        arcpy.CopyFeatures_management(fc, fc + "_sppct")
                        fldct = 1
                        for field in arcpy.ListFields(fc + "_sppct", "SCNTFC_CD*"):
                            arcpy.Select_analysis(fc + "_sppct", fc + "_sppct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                            if int(fldct) > 1:
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                                arcpy.CalculateField_management(fc + "_sppct" + str(fldct), "EST_CVR_RT", "!EST_CVR_RT" + str(fldct) + "!", "PYTHON_9.3")
                            fldct += 1
                        revsppfm = arcpy.FieldMappings()
                        revsppfm.addTable(fc + "_sppct")
                        fclst = arcpy.ListFeatureClasses(fc + "_sppct*")
                        arcpy.Merge_management(fclst, fc + "_spptot", revsppfm)
                        arcpy.DeleteIdentical_management(fc + "_spptot", ["SHAPE", "AREA_TY_NM", "TEMP_TREAT_SITE", "LOC_NM", "TEAM", "PARK_UNIT", "CLIENT", "RECORDER", "ROLE_NM", "TRT_BEG_DT", "TRT_END_DT", "PHNLGY_NM", "DPC_TX", "STOCK_ME", "VEG_UOM_NM", "REVEG_PHNLGY_NM", "SEEDLOT_NR", "RVG_SCNTFC_CD", "NOTES", "SCNTFC_CD", "EST_CVR_RT"])
                        recct = arcpy.GetCount_management(fc + "_spptot").getOutput(0)
                        revspp += int(recct)
                # QC for Photo data
                if "Photo" in fc:
                    arcpy.Select_analysis(fc, fc + "_phdt", "\"PHOTODATE\" IS NULL")
                    recct = arcpy.GetCount_management(fc + "_phdt").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":PHOTODATE is missing values. PHOTODATE is a required field.\n")
                    arcpy.Select_analysis(fc, fc + "_phdtnotnull", "\"PHOTODATE\" IS NOT NULL")
                    arcpy.AddField_management(fc + "_phdtnotnull", "tempdt", "DATE")
                    arcpy.CalculateField_management(fc + "_phdtnotnull", "tempdt", "datetime.datetime.now()", "PYTHON_9.3")
                    arcpy.Select_analysis(fc + "_phdtnotnull", fc + "_tbdtfut", "\"PHOTODATE\" > \"tempdt\"")
                    recct = arcpy.GetCount_management(fc + "_tbdtfut").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":PHOTODATE contains future dates.\n")
                    arcpy.AddField_management(fc + "_phdtnotnull", "dtstatus", "TEXT", "", "", 30)
                    arcpy.CalculateField_management(fc + "_phdtnotnull", "dtstatus", "str(!PHOTODATE!)", "PYTHON_9.3")                        
                    arcpy.Select_analysis(fc + "_phdtnotnull", fc + "tbdttm", "\"dtstatus\" NOT LIKE '%-%' AND \"dtstatus\" NOT LIKE '%/%'")
                    recct = arcpy.GetCount_management(fc + "_tbdttm").getOutput(0)
                    if int(recct) > 0:
                        err.write("ERROR: " + fc + ":PHOTODATE contains invalid values.\n")                        
                    for fields in arcpy.ListFields(fc, "PHOTO*"):
                        fldct = str(field.name[5:])
                        arcpy.Select_analysis(fc, fc + "_phot", "(\"" + field.name + "\" IS NULL AND \"" + field.name + "\" IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')) AND \"PHOTODATE" + str(fldct) + "\" IS NOT NULL")             
                        recct = arcpy.GetCount_management(fc + "_phot").getOutput(0)
                        if int (recct) > 0:
                            err.write("ERROR: " + fc + ":" + field.name + " is missing values. PHOTO is a required if PHOTDATE is populated.\n")
                    for fields in arcpy.ListFields(fc, "PHOTODEG*"):
                        fldct = str(field.name[8:])
                        arcpy.Select_analysis(fc, fc + "_deg", "(\"" + field.name + "\" IS NULL AND \"" + field.name + "\" IN (' ', '')) AND \"PHOTODATE" + str(fldct) + "\" IS NOT NULL")
                        recct = arcpy.GetCount_management(fc + "_deg").getOutput(0)
                        if int(recct) > 0:
                            err.write("ERROR: " + fc + ":" + field.name + " is missing values. PHOTODEG is required if PHOTODATE is populated.\n")
                    arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "domTeam", InAdmin + "\\NISIMS.gdb\\domTEAM", "TEAM_CD", "DESC")
                    arcpy.JoinField_management(fc, "TEAM", InAdmin + "\\NISIMS.gdb\\domTEAM", "TEAM_CD", "TEAM_CD")
                    arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domTEAM")
                    arcpy.Select_analysis(fc, fc + "_team", "\"TEAM_CD\" IS NULL")
                    arcpy.DeleteField_management(fc, "TEAM_CD")
                    recct = arcpy.GetCount_management(fc + "_team").getOutput(0)
                    if int(recct) > 0:
                        arcpy.DeleteIdentical_management(fc + "_team", ["TEAM"])
                        with arcpy.da.SearchCursor(fc + "_team", ["TEAM"]) as cursor:
                            for row in cursor:
                                tmval = str(row[0])
                                err.write("WARNING: " + tmval + " is not an approved team name for " + fc + ". If this is a park team, please ignore. If this is a contractor, be sure the EPMT name is at the beginning of the team name.\n")                    
                    arcpy.DomainToTable_management(InAdmin + "\\NISIMS.gdb", "domParkUnit", InAdmin + "\\NISIMS.gdb\\domPARK_UNIT", "PARK_UNIT_CD", "DESC")
                    arcpy.JoinField_management(fc, "PARK_UNIT", InAdmin + "\\NISIMS.gdb\\domPARK_UNIT", "PARK_UNIT_CD", "PARK_UNIT_CD")
                    arcpy.Delete_management(InAdmin + "\\NISIMS.gdb\\domPARK_UNIT")
                    arcpy.Select_analysis(fc, fc + "_park", "\"PARK_UNIT_CD\" IS NULL")
                    arcpy.DeleteField_management(fc, "PARK_UNIT_CD")
                    recct = arcpy.GetCount_management(fc + "_park").getOuput(0)
                    if int(recct) > 0:
                        arcpy.DeleteIdentical_management(fc + "_park", ["PARK_UNIT"])
                        with arcpy.da.SearchCursor(fc + "_park", ["PARK_UNIT"]) as cursor:
                            for row in cursor:
                                prkval = str(row[0])
                                err.write("ERROR: " + prkval + " is not an approved park unit code for " + fc + ".\n")
                    # Get counts of Photo data
                    recct = arcpy.GetCount_management(fc).getOutput(0)
                    photloc += int(recct)
                    arcpy.CopyFeatures_management(fc, fc + "_photct")
                    fldct = 1
                    for field in arcpy.ListFields(fc + "_photct", "PHOTODATE*"):
                        arcpy.Select_analysis(fc + "_photct", fc + "_photct" + str(fldct), "\"" + field.name + "\" IS NOT NULL AND \"" + field.name + "\" NOT IN ('none', 'None', 'NONE', ' ', '', 'NA', 'Na', 'na')")
                        if int(fldct) > 1:
                            arcpy.CalculateField_management(fc + "_photct" + str(fldct), "PHOTODATE", "!" + field.name + "!", "PYTHON_9.3")
                            arcpy.CalculateField_management(fc + "_photct" + str(fldct), "PHOTODEG", "!PHOTODEG" + str(fldct) + "!", "PYTHON_9.3")
                            arcpy.CalculateField_management(fc + "_photct" + str(fldct), "PREFIX", "!PREFIX" + str(fldct) + "!", "PYTHON_9.3")
                            arcpy.CalculateField_management(fc + "_photct" + str(fldct), "PHOTONUM", "!PHOTONUM" + str(fldct) + "!", "PYTHON_9.3")
                            arcpy.CalculateField_management(fc + "_photct" + str(fldct), "PURPOSE", "!PURPOSE" + str(fldct) + "!", "PYTHON_9.3")
                            arcpy.CalculateField_management(fc + "_photct" + str(fldct), "PHOTO", "!PHOTO" + str(fldct) + "!", "PYTHON_9.3")                            
                        fldct += 1
                    photfm = arcpy.FieldMappings()
                    photfm.addTable(fc + "_photct")
                    fclst = arcpy.ListFeatureClasses(fc + "_photct*")
                    arcpy.Merge_management(fclst, fc + "_phottot", revsppfm)
                    arcpy.DeleteIdentical_management(fc + "_phottot", ["SHAPE", "PREFIX", "PHOTONUM", "PURPOSE", "PHOTODATE", "PHOTO", "PHOTODEG"])
                    recct = arcpy.GetCount_management(fc + "_phottot").getOutput(0)
                    phot += int(recct)                                
    # Write counts to count report
    cts.write("Weed Survey: " + str(wsloc) + "    Weed Survey Species: " + str(wsspp) + "\n")
    cts.write("Weed Infestation: " + str(wiloc) + "    Weed Infestation Land Use: " + str(wilu) + "\n")
    cts.write("Proposed Biological: " + str(pbioloc) + "    Proposed Biological Species: " + str(pbiospp) + "    Proposed Biological Agents: " + str(pbioag) + "    Proposed Biological Cooperators: " + str(pbiocp) + "    Proposed Biological NEPA: " + str(pbionepa) + "\n")
    cts.write("Proposed Chemical: " + str(pchemloc) + "    Proposed Chemical Species: " + str(pchemspp) + "    Proposed Chemical Agents: " + str(pchemag) + "    Proposed Chemical Cooperators: " + str(pchemcp) + "    Proposed Chemical NEPA: " + str(pchemnepa) + "\n")
    cts.write("Proposed Other: " + str(pothloc) + "    Proposed Other Species: " + str(pothspp) + "    Proposed Other Cooperators: " + str(pothcp) + "    Proposed Other NEPA: " + str(pothnepa) + "\n")
    cts.write("Biological: " + str(bioloc) + "    Biological Species: " + str(biospp) + "\n")
    cts.write("Chemical: " + str(chemloc) + "    Chemical Species: " + str(chemspp) + "    Chemical Agents: " + str(chemag) + "    Chemical Adjuvants: " + str(chemadj) + "\n")
    cts.write("Fire: " + str(firloc) + "    Fire Species: " + str(firspp) + "\n")
    cts.write("Manual: " + str(manloc) + "    Manual Species: " + str(manspp) + "\n")
    cts.write("Mechanical: " + str(mechloc) + "    Mechanical Species: " + str(mechspp) + "\n")
    cts.write("Restoration: " + str(resloc) + "    Restoration Species: " + str(resspp) + "    Restoration Activities: " + str(resact) + "\n")
    cts.write("Revegetation: " + str(revloc) + "    Revegetation Species: " + str(revspp) + "\n")
    cts.write("Photo Locations: " + str(photloc) + "    Photos: " + str(phot) + "\n")

    
except:

    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n      " + str(sys.exc_info()[1])
    msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    arcpy.AddError(msgs)
    arcpy.AddError(pymsg)

arcpy.Delete_management("memory")
