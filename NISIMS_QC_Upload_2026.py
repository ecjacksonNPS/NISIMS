#----------------------------------------------------------------------------------------------------------------------
# Name: NISIMS_QC_Upload.py
# Purpose: This script was created to automate the uploading of the NPS NISIMS QC geodatabase. It was created to be
# used by the Data Manager for the EPMT program.
# Author: Jennifer Sieracki
# Created: 2015-08-03 12:58
# Updated: 2026-09-04 14:42 -- Fixes
#----------------------------------------------------------------------------------------------------------------------

# Import modules
import arcpy
import sys
import traceback
import time


def add_records(type, feature, fields, new_feature, table):
    """Purpose: To add records from a feature class to a SDE GDB table
    Parameters:
        type (string): The feature type counted and added
        feature (string): The name of the feature class
        fields (list): The fields to gather from the input feature class
        new_feature (string): The name of the temporary new feature added to the table
        table (string): The name of the SDE table to be appended to
    …
    Return: None
    """
    row_pairs = set()
    with arcpy.da.UpdateCursor(feature, fields) as cursor:
        for row in cursor:
            row_pair = str(row)
            if row_pair in row_pairs:
                cursor.deleteRow()
            else:
                row_pairs.add(row_pair)
    arcpy.CopyRows_management(feature, new_feature)
    survsppin = arcpy.GetCount_management(new_feature).getOutput(0)
    arcpy.AddMessage(type + " Input Count: " + str(survsppin))
    wsspfm = arcpy.FieldMappings()
    wsspfm.addTable(SDEgdb + "\\" + table)
    survsppbef = arcpy.GetCount_management(SDEgdb + "\\dbo." + table).getOutput(0)
    arcpy.Append_management(new_feature, SDEgdb + "\\dbo." + table, "NO_TEST", wsspfm)   
    survsppaft = arcpy.GetCount_management(SDEgdb + "\\dbo." + table).getOutput(0)
    survsppdif = int(survsppaft) - int(survsppbef)
    arcpy.AddMessage(str(survsppdif) + " records added to " + str(table))


def calculate_and_count(original_feature, feature_suffix, field_prefix, temp_feature_prefix):
    """Purpose: To calculate non-null field values in a copied feature class,
    then return their count
    Parameters:
        original_feature (string): The feature to be calculated
        feature_suffix (string): The suffix to be added to the feature
        field_prefix (list): The field prefix to be searched for
        temp_feature_prefix (string): The name of the temporary new feature
    …
    Return: sppcnt (int): the count of all non-null features
    """
    arcpy.CopyFeatures_management(original_feature, original_feature + feature_suffix)
    SppNum = 1
    for field in arcpy.ListFields(original_feature + feature_suffix, field_prefix + "*"):
        arcpy.Select_analysis(original_feature + feature_suffix, temp_feature_prefix + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
        RecNum = arcpy.GetCount_management(temp_feature_prefix + str(SppNum)).getOutput(0)
        if int(RecNum) > 0:
            arcpy.CalculateField_management(temp_feature_prefix + str(SppNum), field_prefix, "!" + field.name + "!", "PYTHON_9.3")
            SppNum += 1
    sppfld = arcpy.ListFeatureClasses(temp_feature_prefix + "*")
    SppCt = len(sppfld)
    sppcnt = 0
    if SppCt > 0:
        arcpy.Append_management(sppfld, original_feature + feature_suffix, "NO_TEST")
        arcpy.Select_analysis(original_feature + feature_suffix, original_feature + feature_suffix + "sel", "\"" + field_prefix + "\"" + " IS NOT NULL")
        sppcnt = arcpy.GetCount_management(original_feature + feature_suffix + "sel").getOutput(0)
    return str(sppcnt)


def main():
    try:
        # Copy spatial reference
        new_spatialref = arcpy.Describe(SDEgdb + "\\dbo.WeedSurveyLocation").spatialReference

        # Copy features to memory
        arcpy.env.workspace = QCgdb
        arcpy.AddMessage("Copying features to memory...")
        for fc in arcpy.ListFeatureClasses():
            arcpy.CopyFeatures_management(fc, "memory/" + fc)

        # Set memory as workspace
        arcpy.env.workspace = "memory"

        # Check for Survey data
        for fc in arcpy.ListFeatureClasses("WeedSurveyData"):
            arcpy.AddMessage("Processing weed survey data.")
            survin = arcpy.GetCount_management("WeedSurveyData").getOutput(0)
            arcpy.AddMessage("Weed Survey Input Count: " + str(survin))
            arcpy.CopyFeatures_management("WeedSurveyData", "WeedSurveyData_fc")
            arcpy.AddField_management("WeedSurveyData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("WeedSurveyData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)          
            wslfm = arcpy.FieldMappings()
            wslfm.addTable(SDEgdb + "\\dbo.WeedSurveyLocation")
            survbef = arcpy.GetCount_management(SDEgdb + "\\dbo.WeedSurveyLocation").getOutput(0)
            arcpy.Append_management("%workspace%\\WeedSurveyData_fc", SDEgdb + "\\dbo.WeedSurveyLocation", "NO_TEST", wslfm)
            survaft = arcpy.GetCount_management(SDEgdb + "\\dbo.WeedSurveyLocation").getOutput(0)
            survdif = int(survaft) - int(survbef)
            arcpy.AddMessage(str(survdif) + " records added to WeedSurveyLocation")


            # Split out SCNTFC_CD fields
            sppcnt = calculate_and_count("WeedSurveyData", "_spp", "SCNTFC_CD", "spp_")     
            if int(sppcnt) > 0:
                add_records("Survey Species", "WeedSurveyData_sppsel", ["SURV_GUID", "SCNTFC_CD"], "spp_all", "WEEDSURVEYSPECIES")

        # Check for Infestation data
        for fc in arcpy.ListFeatureClasses("WeedInfestationData"):
            arcpy.AddMessage("Processing weed infestation data.")
            arcpy.CopyFeatures_management("WeedInfestationData", "WeedInfestationData_fc")
            infin = arcpy.GetCount_management("WeedInfestationData_fc").getOutput(0)
            arcpy.AddMessage("Weed Infestation Input Count: " + str(infin))
            arcpy.CalculateField_management("WeedInfestationData_fc", "NETACRE_ME", "!GRSACRE_ME! * !EST_CVR_RT! / 100", "PYTHON_9.3")
            arcpy.AddField_management("WeedInfestationData_fc", "DelID", "LONG")
            arcpy.CalculateField_management("WeedInfestationData_fc", "DelID", "autoIncrement()", "PYTHON_9.3", count_cb)

            # Calculate currentness
            n=0
            for fc in arcpy.ListFeatureClasses():
                if "WeedSurveyData" in fc:
                    n+=1
                else:
                    n+=0
                if n == 1:
                    arcpy.CreateFeatureclass_management("memory", "WeedInfestationSurvey", "POLYGON", "WeedInfestationData_fc", "", "", new_spatialref)
                    arcpy.Append_management(["WeedInfestationData_fc", "WeedSurveyData_sppsel"], "WeedInfestationSurvey", "NO_TEST")
                else:
                    arcpy.CopyFeatures_management("WeedInfestationData_fc", "WeedInfestationSurvey")
            arcpy.AddField_management("WeedInfestationSurvey", "SCNTFC_CD_upload", "TEXT", "", "", 10)
            arcpy.CalculateField_management("WeedInfestationSurvey", "SCNTFC_CD_upload", "!SCNTFC_CD!", "PYTHON_9.3")
            arcpy.AddField_management("WeedInfestationSurvey", "BEGIN_DT_upload", "DATE")
            arcpy.CalculateField_management("WeedInfestationSurvey", "BEGIN_DT_upload", "!BEGIN_DT!", "PYTHON_9.3")
            arcpy.CopyFeatures_management(SDEgdb + "\\dbo.WeedInfestationLocation", "WeedInfCopy")
            arcpy.SpatialJoin_analysis("WeedInfCopy", "WeedInfestationSurvey", "WeedInfJoin", "JOIN_ONE_TO_MANY", "KEEP_COMMON")
            
            arcpy.AddField_management("WeedInfJoin", "DelID_join", "LONG")
            arcpy.CalculateField_management("WeedInfJoin", "DelID_join", "!DelID!", "PYTHON_9.3")
            arcpy.Select_analysis("WeedInfJoin","WeedInfSel", "\"SCNTFC_CD\" = \"SCNTFC_CD_upload\" AND \"BEGIN_DT\" < \"BEGIN_DT_upload\"")

            arcpy.CalculateField_management("WeedInfSel", "CURRENT_CD", "\"H\"", "PYTHON_9.3")
            arcpy.CalculateField_management("WeedInfSel", "END_DT", "!BEGIN_DT_upload!", "PYTHON_9.3")
            arcpy.AddField_management("WeedInfSel", "CURRENT_CD_join", "TEXT", "", "", 1)
            arcpy.CalculateField_management("WeedInfSel", "CURRENT_CD_join", "!CURRENT_CD!", "PYTHON_9.3")
            arcpy.AddField_management("WeedInfSel", "GUID_TX", "TEXT", "", "", 100)
            arcpy.CalculateField_management("WeedInfSel", "GUID_TX", "!INF_GUID!", "PYTHON_9.3")
            arcpy.DeleteField_management("WeedInfSel", "CURRENT_CD")
            arcpy.analysis.Statistics("WeedInfSel", SDEgdb + "\\dbo.WeedInfSDESum", [["END_DT", "MIN"]], "GUID_TX;CURRENT_CD_join")

            arcpy.JoinField_management(SDEgdb + "\\dbo.WeedInfestationLocation", "INF_GUID", SDEgdb + "\\dbo.WeedInfSDESum", "GUID_TX", ["CURRENT_CD_join", "GUID_TX", "MIN_END_DT"])
            arcpy.CalculateField_management(SDEgdb + "\\dbo.WeedInfestationLocation", "CURRENT_CD", "calccur(!CURRENT_CD_join!, !CURRENT_CD!)", "PYTHON_9.3", curnull)
            arcpy.CalculateField_management(SDEgdb + "\\dbo.WeedInfestationLocation", "END_DT", "Calc(!CURRENT_CD!, !END_DT!, !MIN_END_DT!)", "PYTHON_9.3", endnotnull_cb)
            arcpy.DeleteField_management(SDEgdb + "\\dbo.WeedInfestationLocation", "CURRENT_CD_join;MIN_END_DT;GUID_TX")           
            arcpy.Delete_management(SDEgdb + "\\dbo.WeedInfSDESum")

            arcpy.AddField_management("WeedInfSel", "CURRENT_CD", "TEXT", "", "", 1)
            arcpy.CalculateField_management("WeedInfSel", "CURRENT_CD", "\"C\"", "PYTHON_9.3")
            arcpy.AddField_management("WeedInfSel", "END_DT", "DATE")
            arcpy.CalculateField_management("WeedInfSel", "END_DT", "None", "PYTHON_9.3")
            arcpy.Select_analysis("WeedInfJoin", "WeedInfSel2", "\"SCNTFC_CD\" = \"SCNTFC_CD_upload\" AND \"BEGIN_DT\" > \"BEGIN_DT_upload\"")
            arcpy.CalculateField_management("WeedInfSel2", "CURRENT_CD", "\"H\"", "PYTHON_9.3")
            arcpy.CalculateField_management("WeedInfSel2", "END_DT", "!BEGIN_DT!", "PYTHON_9.3")
            arcpy.Select_analysis("WeedInfJoin", "WeedInfSel3", "\"SCNTFC_CD\" <> \"SCNTFC_CD_upload\"")
            arcpy.CalculateField_management("WeedInfSel3", "CURRENT_CD", "\"C\"", "PYTHON_9.3")
            arcpy.CalculateField_management("WeedInfSel3", "END_DT", "None", "PYTHON_9.3")
            arcpy.Append_management(["WeedInfSel2", "WeedInfSel3"], "WeedInfSel", "NO_TEST")
            arcpy.Statistics_analysis("WeedInfSel", "WeedInfSum", [["END_DT", "MIN"]], "DelID_join")
            arcpy.AddField_management("WeedInfSum", "CURRENT_CD_sum", "TEXT", "", "", 1)
            arcpy.CalculateField_management("WeedInfSum", "CURRENT_CD_sum", "Calc(!MIN_END_DT!)", "PYTHON_9.3", send_cb)
            arcpy.JoinField_management("WeedInfestationData_fc", "DelID", "WeedInfSum", "DelID_join", ["CURRENT_CD_sum", "MIN_END_DT"])
            arcpy.CalculateField_management("WeedInfestationData_fc", "CURRENT_CD", "!CURRENT_CD_sum!", "PYTHON_9.3")
            arcpy.CalculateField_management("WeedInfestationData_fc", "END_DT", "!MIN_END_DT!", "PYTHON_9.3")
            arcpy.CalculateField_management("WeedInfestationData_fc", "CURRENT_CD", "calcnull(!CURRENT_CD!)", "PYTHON_9.3", null_cb)
            arcpy.DeleteField_management("WeedInfestationData_fc", "CURRENT_CD_sum;MIN_END_DT;DelID_join")

            # Calculate upload date
            arcpy.AddField_management("WeedInfestationData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("WeedInfestationData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)

            # Append Infestation Data
            wilfm = arcpy.FieldMappings()
            wilfm.addTable(SDEgdb + "\\dbo.WeedInfestationLocation")
            infbef = arcpy.GetCount_management(SDEgdb + "\\dbo.WeedInfestationLocation").getOutput(0)
            arcpy.Append_management("WeedInfestationData_fc", SDEgdb + "\\dbo.WeedInfestationLocation", "NO_TEST", wilfm)
            infaft = arcpy.GetCount_management(SDEgdb + "\\dbo.WeedInfestationLocation").getOutput(0)
            infdif = int(infaft) - int(infbef)
            arcpy.AddMessage(str(infdif) + " records added to WeedInfestationLocation")
                

            # Split out LU_CTGY_NM fields
            arcpy.CopyFeatures_management("WeedInfestationData", "WeedInfestationData_lu")
            LuNum = 1
            for field in arcpy.ListFields("WeedInfestationData_lu", "LU_CTGY_NM*"):
                arcpy.Select_analysis("WeedInfestationData_lu", "lutb2_" + str(LuNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("lutb2_" + str(LuNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("lutb2_" + str(LuNum), "LU_CTGY_NM", "!" + field.name + "!", "PYTHON_9.3")
                    LuNum += 1
            lufld = arcpy.ListFeatureClasses("lutb2_*")
            arcpy.CreateFeatureclass_management("memory", "WeedInfestationData_copy", "POLYGON", "WeedInfestationData_lu", "", "", new_spatialref)
            arcpy.Append_management(lufld, "WeedInfestationData_copy", "NO_TEST")
            arcpy.Select_analysis("WeedInfestationData_copy", "WeedInfestationData_copy2", "\"LU_CTGY_NM\" IS NOT NULL")
            arcpy.CopyRows_management("WeedInfestationData_copy2", "lutb_all")
            influin = arcpy.GetCount_management("lutb_all").getOutput(0)
            arcpy.AddMessage("Weed Infestation Land Use Input Count: " + str(influin))
            wichfm = arcpy.FieldMappings()
            wichfm.addTable(SDEgdb + "\\dbo.ASSOCIATEDCHARACTERISTIC")
            influbef = arcpy.GetCount_management(SDEgdb + "\\dbo.ASSOCIATEDCHARACTERISTIC").getOutput(0)
            arcpy.Append_management("lutb_all", SDEgdb + "\\dbo.ASSOCIATEDCHARACTERISTIC", "NO_TEST", wichfm)
            influaft = arcpy.GetCount_management(SDEgdb + "\\dbo.ASSOCIATEDCHARACTERISTIC").getOutput(0)
            infludif = int(influaft) - int(influbef)
            arcpy.AddMessage(str(infludif) + " records added to ASSOCIATEDCHARACTERISTIC")

        # Check for proposed biological data
        for fc in arcpy.ListFeatureClasses("ProposedBiologicalData"):
            arcpy.AddMessage("Processing proposed biological data.")
            arcpy.CopyFeatures_management("ProposedBiologicalData", "ProposedBiologicalData_fc")
            propbioin = arcpy.GetCount_management("ProposedBiologicalData_fc").getOutput(0)
            arcpy.AddMessage("Proposed Biological Data Input Count: " + str(propbioin))
            arcpy.AddField_management("ProposedBiologicalData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("ProposedBiologicalData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)
            pbtfm = arcpy.FieldMappings()
            pbtfm.addTable(SDEgdb + "\\dbo.ProposedTreatmentLocation")
            propbiobef = arcpy.GetCount_management(SDEgdb + "\\dbo.ProposedTreatmentLocation").getOutput(0)
            arcpy.Append_management("ProposedBiologicalData_fc", SDEgdb + "\\dbo.ProposedTreatmentLocation", "NO_TEST", pbtfm)
            propbioaft = arcpy.GetCount_management(SDEgdb + "\\dbo.ProposedTreatmentLocation").getOutput(0)
            propbiodif = int(propbioaft) - int(propbiobef)
            arcpy.AddMessage(str(propbiodif) + " records added to ProposedTreatmentLocation")

            # Split out SCNTFC_CD fields
            sppcnt = calculate_and_count("ProposedBiologicalData", "_spp", "SCNTFC_CD", "pbiotb2_")
            if int(sppcnt) > 0:
                add_records("Proposed Biological Species", "ProposedBiologicalData_sppsel", ["SCNTFC_CD", "PROP_TRT_GUID"], "pbiotb_all", "PROPOSALSPECIES")

            # Split out BIO_SCNTFC_CD fields
            arcpy.CopyFeatures_management("ProposedBiologicalData", "ProposedBiologicalData_biospp")
            BsppNum = 1
            for field in arcpy.ListFields("ProposedBiologicalData_biospp", "BIO_SCNTFC_CD*"):
                arcpy.Select_analysis("ProposedBiologicalData_biospp", "pbiotb4_" + str(BsppNum), "\"" + field.name + "\"" + " IS NOT NULL")            
                RecNum = arcpy.GetCount_management("pbiotb4_" + str(BsppNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "BIO_SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                    BioNum = str(field.name)
                    BioNum = BioNum.strip("BIO_SCNTFC_CD")
                    BioUse = str("SPC_USE_QY" + BioNum)
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "SPC_USE_QY", "!" + BioUse + "!", "PYTHON_9.3")
                    BioMat = str("HSTMATL_NM" + BioNum)
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "HSTMATL_NM", "!" + BioMat + "!", "PYTHON_9.3")
                    BioPDt = str("PRMT_DT" + BioNum)
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "PRMT_DT", "!" + BioPDt + "!", "PYTHON_9.3")
                    BioPRq = str("PRMTREQ_FL" + BioNum)
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "PRMTREQ_FL", "!" + BioPRq + "!", "PYTHON_9.3")
                    BioLCy = str("LFCYCLE_NM" + BioNum)
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "LFCYCLE_NM", "!" + BioLCy + "!", "PYTHON_9.3")
                    BioCty = str("CLLCNTY_NM" + BioNum)
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "CLLCNTY_NM", "!" + BioCty + "!", "PYTHON_9.3")
                    BioSta = str ("CLSTATE_CD" + BioNum)
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "CLSTATE_CD", "!" + BioSta + "!", "PYTHON_9.3")
                    BioPmt = str("PRMT_NR" + BioNum)
                    arcpy.CalculateField_management("pbiotb4_" + str(BsppNum), "PRMT_NR", "!" + BioPmt + "!", "PYTHON_9.3")
                    BsppNum += 1
            bsppfld = arcpy.ListFeatureClasses("pbiotb4_*")
            arcpy.Append_management(bsppfld, "ProposedBiologicalData_biospp", "NO_TEST")
            arcpy.Select_analysis("ProposedBiologicalData_biospp", "ProposedBiologicalData_biosppsel", "\"BIO_SCNTFC_CD\" IS NOT NULL")
            bsppcnt = arcpy.GetCount_management("ProposedBiologicalData_biosppsel").getOutput(0)
            if int(bsppcnt) > 0:
                add_records("Proposed Biological Component", "ProposedBiologicalData_biosppsel", ["BIO_SCNTFC_CD", "PROP_TRT_GUID"], "pbiotb_all", "PROPOSALBIOCOMPONENTAGENT")
            # Split out COOP_PERS fields
            coopcnt = calculate_and_count("ProposedBiologicalData", "_coop", "COOP_PERS", "pbiotb6_")
            if int(coopcnt) > 0:
                add_records("Proposed Biological Cooperator", "ProposedBiologicalData_coopsel", ["COOP_PERS", "PROP_TRT_GUID"], "pbiotb_all", "PROPOSALCOOPERATOR")

            # Split out NEPA_NR fields
            nepacnt = calculate_and_count("ProposedBiologicalData", "_nepa", "NEPA_NR", "pbiotb8_")
            if int(nepacnt) > 0:
                add_records("Proposed NEPA Component", "ProposedBiologicalData_nepasel", ["NEPA_NR", "PROP_TRT_GUID"], "pbiotb_all", "TREATMENTPROPOSALNUMBERS")

        # Check for proposed chemical data
        for fc in arcpy.ListFeatureClasses("ProposedChemicalData"):
            arcpy.AddMessage("Processing proposed chemical data.")
            arcpy.CopyFeatures_management("ProposedChemicalData", "ProposedChemicalData_fc")
            propchemin = arcpy.GetCount_management("ProposedChemicalData_fc").getOutput(0)
            arcpy.AddMessage("Proposed Chemical Data Input Count: " + str(propchemin))
            arcpy.AddField_management("ProposedChemicalData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("ProposedChemicalData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)      
            pctfm = arcpy.FieldMappings()
            pctfm.addTable(SDEgdb + "\\dbo.ProposedTreatmentLocation")
            propchembef = arcpy.GetCount_management(SDEgdb + "\\dbo.ProposedTreatmentLocation").getOutput(0)
            arcpy.Append_management("ProposedChemicalData_fc", SDEgdb + "\\dbo.ProposedTreatmentLocation", "NO_TEST", pctfm)
            propchemaft = arcpy.GetCount_management(SDEgdb + "\\dbo.ProposedTreatmentLocation").getOutput(0)
            propchemdif = int(propchemaft) - int(propchembef)
            arcpy.AddMessage(str(propchemdif) + " records added to ProposedTreatmentLocation")

            # Split out SCNTFC_CD fields
            sppcnt = calculate_and_count("ProposedChemicalData", "_spp", "SCNTFC_CD", "pchemtb2_")
            if int(sppcnt) > 0:
                add_records("Proposed Chemical Species", "ProposedChemicalData_sppsel", ["SCNTFC_CD", "PROP_TRT_GUID"], "pchemtb_all", "PROPOSALSPECIES")

            # Split out TRADE_NM fields
            arcpy.CopyFeatures_management("ProposedChemicalData", "ProposedChemicalData_chemag")
            CagNum = 1
            for field in arcpy.ListFields("ProposedChemicalData_chemag", "TRADE_NM*"):
                arcpy.Select_analysis("ProposedChemicalData_chemag", "pchemtb4_" + str(CagNum), "\"" + field.name + "\"" + " IS NOT NULL")            
                RecNum = arcpy.GetCount_management("pchemtb4_" + str(CagNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "TRADE_NM", "!" + field.name + "!", "PYTHON_9.3")
                    ChemNum = str(field.name)
                    ChemNum = ChemNum.strip("TRADE_NM")
                    ChemMnf = str("MNFCTR_NM" + ChemNum)
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "MNFCTR_NM", "!" + ChemMnf + "!", "PYTHON_9.3")
                    ChemSit = str("SITE_TX" + ChemNum)
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "SITE_TX", "!" + ChemSit + "!", "PYTHON_9.3")
                    ChemArt = str("APP_RT_TX" + ChemNum)
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "APP_RT_TX", "!" + ChemArt + "!", "PYTHON_9.3")
                    ChemAlo = str("APP_AMT_LOW" + ChemNum)
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "APP_AMT_LOW", "!" + ChemAlo + "!", "PYTHON_9.3")
                    ChemAhi = str("APP_AMT_HIGH" + ChemNum)
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "APP_AMT_HIGH", "!" + ChemAhi + "!", "PYTHON_9.3")
                    ChemTid = str("TRT_ID" + ChemNum)
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "TRT_ID", "!" + ChemTid + "!", "PYTHON_9.3")
                    ChemRol = str("ROLE_NM" + ChemNum)
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "ROLE_NM", "!" + ChemRol + "!", "PYTHON_9.3")
                    ChemCrt = str("CERT_NR" + ChemNum)
                    arcpy.CalculateField_management("pchemtb4_" + str(CagNum), "CERT_NR", "!" + ChemCrt + "!", "PYTHON_9.3")
                    CagNum += 1
            Cagfld = arcpy.ListFeatureClasses("pchemtb4_*")
            arcpy.Append_management(Cagfld, "ProposedChemicalData_chemag", "NO_TEST")
            arcpy.Select_analysis("ProposedChemicalData_chemag", "ProposedChemicalData_chemagsel", "\"TRADE_NM\" IS NOT NULL")
            bsppcnt = arcpy.GetCount_management("ProposedChemicalData_chemagsel").getOutput(0)
            if int(bsppcnt) > 0:
                add_records("Proposed Chemical Component", "ProposedChemicalData_chemagsel", ["TRADE_NM", "PROP_TRT_GUID"], "pchemtb_all", "PROPOSALCHEMCOMPONENTAGENT")

            # Split out COOP_PERS fields
            coopcnt = calculate_and_count("ProposedChemicalData", "_coop", "COOP_PERS", "pchemtb6_")
            if int(coopcnt) > 0:
                add_records("Proposed Chemical Cooperator", "ProposedChemicalData_coopsel", ["COOP_PERS", "PROP_TRT_GUID"], "pchemtb_all", "PROPOSALCOOPERATOR")
            # Split out NEPA_NR fields
            nepacnt = calculate_and_count("ProposedChemicalData", "_nepa", "NEPA_NR", "pchemtb8_")
            if int(nepacnt) > 0:
                add_records("Proposed Chemical NEPA", "ProposedChemicalData_nepasel", ["NEPA_NR", "PROP_TRT_GUID"], "pchemtb_all", "TREATMENTPROPOSALNUMBERS")
        # Check for proposed other data
        for fc in arcpy.ListFeatureClasses("ProposedOtherData"):
            arcpy.AddMessage("Processing proposed other data.")
            arcpy.CopyFeatures_management("ProposedOtherData", "ProposedOtherData_fc")
            propothin = arcpy.GetCount_management("ProposedOtherData_fc").getOutput(0)
            arcpy.AddMessage("Proposed Other Data Input Count: " + str(propothin))
            arcpy.AddField_management("ProposedOtherData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("ProposedOtherData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)         
            pctfm = arcpy.FieldMappings()
            pctfm.addTable(SDEgdb + "\\dbo.ProposedTreatmentLocation")
            propothbef = arcpy.GetCount_management(SDEgdb + "\\dbo.ProposedTreatmentLocation").getOutput(0)
            arcpy.Append_management("ProposedOtherData_fc", SDEgdb + "\\dbo.ProposedTreatmentLocation", "NO_TEST", pctfm)
            propothaft = arcpy.GetCount_management(SDEgdb + "\\dbo.ProposedTreatmentLocation").getOutput(0)
            propothdif = int(propothaft) - int(propothbef)
            arcpy.AddMessage(str(propothdif) + " records added to ProposedTreatmentLocation")

            # Split out SCNTFC_CD fields
            sppcnt = calculate_and_count("ProposedOtherData", "_spp", "SCNTFC_CD", "pothtb2_")
            if int(sppcnt) > 0:
                add_records("Proposed Other Species", "ProposedOtherData_sppsel", ["SCNTFC_CD", "PROP_TRT_GUID"], "pothtb_all", "PROPOSALSPECIES")
            # Split out COOP_PERS fields
            coopcnt = calculate_and_count("ProposedOtherData", "_coop", "COOP_PERS", "pothtb6_")
            if int(coopcnt) > 0:
                add_records("Proposed Other Cooperator", "ProposedOtherData_coopsel", ["COOP_PERS", "PROP_TRT_GUID"], "pothtb_all", "PROPOSALCOOPERATOR")
            # Split out NEPA_NR fields
            nepacnt = calculate_and_count("ProposedOtherData", "_nepa", "NEPA_NR", "pothtb8_")
            if int(nepacnt) > 0:
                add_records("Proposed Other NEPA", "ProposedOtherData_nepasel", ["NEPA_NR", "PROP_TRT_GUID"], "pothtb_all", "TREATMENTPROPOSALNUMBERS")
        # Check for biological treatment data
        for fc in arcpy.ListFeatureClasses("BiologicalTreatmentData"):
            arcpy.AddMessage("Processing biological data.")
            arcpy.CopyFeatures_management("BiologicalTreatmentData", "BiologicalTreatmentData_fc")
            bioin = arcpy.GetCount_management("BiologicalTreatmentData_fc").getOutput(0)
            arcpy.AddMessage("Biological Treatment Data Input Count: " + str(bioin))
            arcpy.AddField_management("BiologicalTreatmentData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("BiologicalTreatmentData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb) 
            biofm = arcpy.FieldMappings()
            biofm.addTable(SDEgdb + "\\dbo.TreatmentComponentLocation")
            biobef = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            arcpy.Append_management("BiologicalTreatmentData_fc", SDEgdb + "\\dbo.TreatmentComponentLocation", "NO_TEST", biofm)        
            bioaft = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            biodif = int(bioaft) - int(biobef)
            arcpy.AddMessage(str(biodif) + " records added to TreatmentComponentLocation")
            
            # Merge to BIOLOGICALCOMPONENT
            arcpy.CopyFeatures_management("BiologicalTreatmentData_fc", "BiologicalTreatmentData_biocomp")
            arcpy.AddField_management("BiologicalTreatmentData_biocomp", "tot_est_cvr_rt", "DOUBLE")
            arcpy.AddField_management("BiologicalTreatmentData_biocomp", "temp_fld", "DOUBLE")
            for field in arcpy.ListFields("BiologicalTreatmentData_biocomp", "EST_CVR_RT*"):
                arcpy.CalculateField_management("BiologicalTreatmentData_biocomp", "temp_fld", "!" + field.name + "!", "PYTHON_9.3")
                arcpy.CalculateField_management("BiologicalTreatmentData_biocomp", "tot_est_cvr_rt", "cvrac(!tot_est_cvr_rt!,!temp_fld!)", "PYTHON_9.3", totaccalc)
            arcpy.DeleteField_management("BiologicalTreatmentData_biocomp", "tempfld")
            arcpy.CalculateField_management("BiologicalTreatmentData_biocomp", "CVRAREA_ME", "!CLCACRE_ME! * !tot_est_cvr_rt! / 100", "PYTHON_9.3")
            add_records("Biological Component", "BiologicalTreatmentData_biocomp", ["BIO_SCNTFC_CD", "TRT_GUID"], "biotb_all", "BIOLOGICALCOMPONENT")        
            # Split out SCNTFC_CD fields
            arcpy.CopyFeatures_management("BiologicalTreatmentData", "BiologicalTreatmentData_spp")
            SppNum = 1
            for field in arcpy.ListFields("BiologicalTreatmentData_spp", "SCNTFC_CD*"):
                arcpy.Select_analysis("BiologicalTreatmentData_spp", "biotbspp_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("biotbspp_" + str(SppNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("biotbspp_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                    SpNum = str(field.name)
                    SpNum = SpNum.strip("SCNTFC_CD")
                    SpCov = str("EST_CVR_RT" + SpNum)
                    arcpy.CalculateField_management("biotbspp_" + str(SppNum), "EST_CVR_RT", "!" + SpCov + "!", "PYTHON_9.3")
                    SppNum += 1
            sppfld = arcpy.ListFeatureClasses("biotbspp_*")
            arcpy.Append_management(sppfld, "BiologicalTreatmentData_spp", "NO_TEST")
            arcpy.Select_analysis("BiologicalTreatmentData_spp", "BiologicalTreatmentData_sppsel", "\"SCNTFC_CD\" IS NOT NULL")
            sppcnt = arcpy.GetCount_management("BiologicalTreatmentData_sppsel").getOutput(0)
            if int(sppcnt) > 0:
                arcpy.AddField_management("BiologicalTreatmentData_sppsel", "cvrrttx", "TEXT", "", "", 20)
                arcpy.CalculateField_management("BiologicalTreatmentData_sppsel", "cvrrttx", "!EST_CVR_RT!", "PYTHON_9.3")
                add_records("Biological Species", "BiologicalTreatmentData_sppsel", ["SCNTFC_CD", "cvrrttx", "TRT_GUID"], "biotb_all", "TREATMENTSPECIES")           
        # Check for chemical treatment data
        for fc in arcpy.ListFeatureClasses("ChemicalTreatmentData"):
            arcpy.AddMessage("Processing chemical data.")   
            arcpy.CopyFeatures_management("ChemicalTreatmentData", "ChemicalTreatmentData_fc")
            chemin = arcpy.GetCount_management("ChemicalTreatmentData_fc").getOutput(0)
            arcpy.AddMessage("Chemical Data Input Count: " + str(chemin))
            arcpy.AddField_management("ChemicalTreatmentData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("ChemicalTreatmentData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)
            chemfm = arcpy.FieldMappings()
            chemfm.addTable(SDEgdb + "\\dbo.TreatmentComponentLocation")
            chembef = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            arcpy.Append_management("ChemicalTreatmentData_fc", SDEgdb + "\\dbo.TreatmentComponentLocation", "NO_TEST", chemfm)
            chemaft = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            chemdif = int(chemaft) - int(chembef)
            arcpy.AddMessage(str(chemdif) + " records added to TreatmentComponentLocation")
            
            # Merge to CHEMICALCOMPONENT
            arcpy.CopyFeatures_management("ChemicalTreatmentData_fc", "ChemicalTreatmentData_chemcomp")
            arcpy.AddField_management("ChemicalTreatmentData_chemcomp", "tot_est_cvr_rt", "DOUBLE")
            arcpy.AddField_management("ChemicalTreatmentData_chemcomp", "temp_fld", "DOUBLE")
            for field in arcpy.ListFields("ChemicalTreatmentData_chemcomp", "EST_CVR_RT*"):
                arcpy.CalculateField_management("ChemicalTreatmentData_chemcomp", "temp_fld", "!" + field.name + "!", "PYTHON_9.3")
                arcpy.CalculateField_management("ChemicalTreatmentData_chemcomp", "tot_est_cvr_rt", "cvrac(!tot_est_cvr_rt!,!temp_fld!)", "PYTHON_9.3", totaccalc)
            arcpy.DeleteField_management("ChemicalTreatmentData_chemcomp", "tempfld")
            arcpy.CalculateField_management("ChemicalTreatmentData_chemcomp", "ESTACRE_ME", "!CLCACRE_ME! * !tot_est_cvr_rt! / 100", "PYTHON_9.3")
            add_records("Chemical Component", "ChemicalTreatmentData_chemcomp", ["TRT_GUID"], "chemtb_all", "CHEMICALCOMPONENT")        
            # Split out TRADE_NM fields
            arcpy.CopyFeatures_management("ChemicalTreatmentData", "ChemicalTreatmentData_chemag")
            arcpy.CreateFeatureclass_management("memory", "ChemicalTreatmentData_chemag2", "POLYGON", "ChemicalTreatmentData_chemag", "", "", new_spatialref)
            HerbNum = 1
            for field in arcpy.ListFields("ChemicalTreatmentData_chemag", "TRADE_NM*"):
                arcpy.Select_analysis("ChemicalTreatmentData_chemag", "chemtb5_" + str(HerbNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("chemtb5_" + str(HerbNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "TRADE_NM", "!" + field.name + "!", "PYTHON_9.3")
                    ChemNum = str(field.name)
                    ChemNum = ChemNum.strip("TRADE_NM")
                    ChemAgRt = str("AGT_APP_RT" + ChemNum)
                    arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "AGT_APP_RT", "!" + ChemAgRt + "!", "PYTHON_9.3")
                    ChemApU = str("APP_UOM_NM" + ChemNum)
                    arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "APP_UOM_NM", "!" + ChemApU + "!", "PYTHON_9.3")
                    ChemMfr = str("MNFCTR_NM" + ChemNum)
                    arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "MNFCTR_NM", "!" + ChemMfr + "!", "PYTHON_9.3")
                    ChemQty = str("ACTLUSE_QY" + ChemNum)
                    arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "ACTLUSE_QY", "!" + ChemQty + "!", "PYTHON_9.3")
                    ChemQyU = str("AGT_UOM_NM" + ChemNum)
                    arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "AGT_UOM_NM", "!" + ChemQyU + "!", "PYTHON_9.3")
                    ChemEPA = str("EPAREGISTRATIONNUMBER" + ChemNum)
                    arcpy.CalculateField_management("chemtb5_" + str(HerbNum), "EPAREGISTRATIONNUMBER", "!" + ChemEPA + "!", "PYTHON_9.3")
                    HerbNum += 1
            herbfld = arcpy.ListFeatureClasses("chemtb5_*")
            arcpy.Append_management(herbfld, "ChemicalTreatmentData_chemag2", "NO_TEST")
            arcpy.Select_analysis("ChemicalTreatmentData_chemag2", "ChemicalTreatmentData_chemag2sel", "\"TRADE_NM\" IS NOT NULL")
            herbcnt = arcpy.GetCount_management("ChemicalTreatmentData_chemag2sel").getOutput(0)
            if int(herbcnt) > 0:
                add_records("Chemical Agent", "ChemicalTreatmentData_chemag2sel", ["TRADE_NM", "AGT_APP_RT", "APP_UOM_NM", "MNFCTR_NM", "TRT_GUID"], "chemtb_all", "CHEMICALCOMPCONTROLAGENT")            
            # Split out ADJ_TRADE_NM
            arcpy.CopyFeatures_management("ChemicalTreatmentData", "ChemicalTreatmentData_chemadj")
            arcpy.AddField_management("ChemicalTreatmentData_chemadj", "ACTLUSE_QTY", "DOUBLE")
            arcpy.CreateFeatureclass_management("memory", "ChemicalTreatmentData_chemadj2", "POLYGON", "ChemicalTreatmentData_chemadj", "", "", new_spatialref)
            AdjNum = 1
            for field in arcpy.ListFields("ChemicalTreatmentData_chemadj", "ADJ_TRADE_NM*"): 
                arcpy.Select_analysis("ChemicalTreatmentData_chemadj", "chemtb7_" + str(AdjNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("chemtb7_" + str(AdjNum)).getOutput(0)
                if int(RecNum) > 0:
                    AdjNR = str(field.name)
                    AdjNR = AdjNR.strip("ADJ_TRADE_NM")
                    arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "TRADE_NM", "!" + field.name + "!", "PYTHON_9.3")
                    AdjUnit = str("ADJ_AGT_UOM_NM" + AdjNR) 
                    arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "AGT_UOM_NM", "!" + AdjUnit + "!", "PYTHON_9.3")
                    AdjAgRt = str("ADJ_AGT_APP_RT" + AdjNR)
                    arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "AGT_APP_RT", "!" + AdjAgRt + "!", "PYTHON_9.3")
                    AdjApU = str("ADJ_APP_UOM_NM" + AdjNR)
                    arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "APP_UOM_NM", "!" + AdjApU + "!", "PYTHON_9.3")
                    AdjAct = str("ADJ_ACTLUSE_QTY" + AdjNR)
                    arcpy.CalculateField_management("chemtb7_" + str(AdjNum), "ACTLUSE_QTY", "!" + AdjAct + "!", "PYTHON_9.3")
                    AdjNum += 1
            adjfld = arcpy.ListFeatureClasses("chemtb7_*")
            adjct = len(adjfld)
            if adjct > 0:
                arcpy.Append_management(adjfld, "ChemicalTreatmentData_chemadj2", "NO_TEST")
                arcpy.Select_analysis("ChemicalTreatmentData_chemadj2", "ChemicalTreatmentData_chemadj2sel", "\"TRADE_NM\" IS NOT NULL")
                adjcnt = arcpy.GetCount_management("ChemicalTreatmentData_chemadj2sel").getOutput(0)
                if int(adjcnt) > 0:
                    add_records("Chemical Adjuvant", "ChemicalTreatmentData_chemadj2sel", ["TRT_GUID", "CONAGT_GUID", "AGT_UOM_NM", "ACTLUSE_QTY", "TRADE_NM", "AGT_APP_RT", "APP_UOM_NM"], "chemtb_all", "ADJUVANTCOMPONENTAGENT")                
            # Split out SCNTFC_CD fields
            arcpy.CopyFeatures_management("ChemicalTreatmentData", "ChemicalTreatmentData_spp")
            SppNum = 1
            for field in arcpy.ListFields("ChemicalTreatmentData_spp", "SCNTFC_CD*"):
                arcpy.Select_analysis("ChemicalTreatmentData_spp", "chemtbspp_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("chemtbspp_" + str(SppNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("chemtbspp_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                    SpNum = str(field.name)
                    SpNum = SpNum.strip("SCNTFC_CD")
                    SpCov = str("EST_CVR_RT" + SpNum)
                    arcpy.CalculateField_management("chemtbspp_" + str(SppNum), "EST_CVR_RT", "!" + SpCov + "!", "PYTHON_9.3")
                    SppNum += 1
            sppfld = arcpy.ListFeatureClasses("chemtbspp_*")
            arcpy.Append_management(sppfld, "ChemicalTreatmentData_spp", "NO_TEST")
            arcpy.Select_analysis("ChemicalTreatmentData_spp", "ChemicalTreatmentData_sppsel", "\"SCNTFC_CD\" IS NOT NULL")
            sppcnt = arcpy.GetCount_management("ChemicalTreatmentData_sppsel").getOutput(0)
            if int(sppcnt) > 0:
                arcpy.AddField_management("ChemicalTreatmentData_sppsel", "cvrrttx", "TEXT", "", "", 20)
                arcpy.CalculateField_management("ChemicalTreatmentData_sppsel", "cvrrttx", "!EST_CVR_RT!", "PYTHON_9.3") 
                add_records("Chemical Species", "ChemicalTreatmentData_sppsel", ["SCNTFC_CD", "cvrrttx", "TRT_GUID"], "chemtb_all", "TREATMENTSPECIES")            
        # Check for fire treatment data
        for fc in arcpy.ListFeatureClasses("FireTreatmentData"):
            arcpy.AddMessage("Processing fire data.")
            arcpy.CopyFeatures_management("FireTreatmentData", "FireTreatmentData_fc")
            firin = arcpy.GetCount_management("FireTreatmentData_fc").getOutput(0)
            arcpy.AddMessage("Fire Data Input Count: " + str(firin))
            arcpy.AddField_management("FireTreatmentData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("FireTreatmentData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)
            firefm = arcpy.FieldMappings()
            firefm.addTable(SDEgdb + "\\dbo.TreatmentComponentLocation")
            firbef = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            arcpy.Append_management("FireTreatmentData_fc", SDEgdb + "\\dbo.TreatmentComponentLocation", "NO_TEST", firefm)
            firaft = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            firdif = int(firaft) - int(firbef)
            arcpy.AddMessage(str(firdif) + " records added to TreatmentComponentLocation")
            
            # Merge to FIRECOMPONENT
            arcpy.CopyFeatures_management("FireTreatmentData_fc", "FireTreatmentData_firecomp")
            add_records("Fire Component", "FireTreatmentData_firecomp", ["INTNSTY_NM", "FUELMDL_TX", "TRT_GUID"], "firetb2", "FIRECOMPONENT")        
            # Split out SCNTFC_CD fields
            arcpy.CopyFeatures_management("FireTreatmentData", "FireTreatmentData_spp")
            SppNum = 1
            for field in arcpy.ListFields("FireTreatmentData_spp", "SCNTFC_CD*"):
                arcpy.Select_analysis("FireTreatmentData_spp", "firetbspp_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("firetbspp_" + str(SppNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("firetbspp_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                    SpNum = str(field.name)
                    SpNum = SpNum.strip("SCNTFC_CD")
                    SpCov = str("EST_CVR_RT" + SpNum)
                    arcpy.CalculateField_management("firetbspp_" + str(SppNum), "EST_CVR_RT", "!" + SpCov + "!", "PYTHON_9.3")
                    SppNum += 1
            sppfld = arcpy.ListFeatureClasses("firetbspp_*")
            arcpy.Append_management(sppfld, "FireTreatmentData_spp", "NO_TEST")
            arcpy.Select_analysis("FireTreatmentData_spp", "FireTreatmentData_sppsel", "\"SCNTFC_CD\" IS NOT NULL")
            sppcnt = arcpy.GetCount_management("FireTreatmentData_sppsel").getOutput(0)
            if int(sppcnt) > 0:
                arcpy.AddField_management("FireTreatmentData_sppsel", "cvrrttx", "TEXT", "", "", 20)
                arcpy.CalculateField_management("FireTreatmentData_sppsel", "cvrrttx", "!EST_CVR_RT!", "PYTHON_9.3")   
                add_records("Fire Species", "FireTreatmentData_sppsel", ["SCNTFC_CD", "cvrrttx", "TRT_GUID"], "firetb_all", "TREATMENTSPECIES")
                
        # Check for manual treatment data
        for fc in arcpy.ListFeatureClasses("ManualTreatmentData"):
            arcpy.AddMessage("Processing manual data.")
            arcpy.CopyFeatures_management("ManualTreatmentData", "ManualTreatmentData_fc")
            manin = arcpy.GetCount_management("ManualTreatmentData_fc").getOutput(0)
            arcpy.AddMessage("Manual Data Input Count: " + str(manin))
            arcpy.AddField_management("ManualTreatmentData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("ManualTreatmentData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)
            manfm = arcpy.FieldMappings()
            manfm.addTable(SDEgdb + "\\dbo.TreatmentComponentLocation")
            manbef = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            arcpy.Append_management("ManualTreatmentData_fc", SDEgdb + "\\dbo.TreatmentComponentLocation", "NO_TEST", manfm)
            manaft = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            mandif = int(manaft) - int(manbef)
            arcpy.AddMessage(str(mandif) + " records added to TreatmentComponentLocation")
            
            # Merge to MANUALCOMPONENT
            arcpy.CopyFeatures_management("ManualTreatmentData_fc", "ManualTreatmentData_mancomp")        
            arcpy.AddField_management("ManualTreatmentData_mancomp", "tot_est_cvr_rt", "DOUBLE")
            arcpy.AddField_management("ManualTreatmentData_mancomp", "temp_fld", "DOUBLE")
            for field in arcpy.ListFields("ManualTreatmentData_mancomp", "EST_CVR_RT*"):
                arcpy.CalculateField_management("ManualTreatmentData_mancomp", "temp_fld", "!" + field.name + "!", "PYTHON_9.3")
                arcpy.CalculateField_management("ManualTreatmentData_mancomp", "tot_est_cvr_rt", "cvrac(!tot_est_cvr_rt!,!temp_fld!)", "PYTHON_9.3", totaccalc)
            arcpy.DeleteField_management("ManualTreatmentData_mancomp", "tempfld")
            arcpy.CalculateField_management("ManualTreatmentData_mancomp", "MANLCMP_ME", "!CLCACRE_ME! * !tot_est_cvr_rt! / 100", "PYTHON_9.3")
            add_records("Manual Component", "ManualTreatmentData_mancomp", ["MANL_CL_NM", "TRT_GUID"], "mantb2", "MANUALCOMPONENT")        
            # Split out SCNTFC_CD fields
            arcpy.CopyFeatures_management("ManualTreatmentData", "ManualTreatmentData_spp")
            SppNum = 1
            for field in arcpy.ListFields("ManualTreatmentData_spp", "SCNTFC_CD*"):
                arcpy.Select_analysis("ManualTreatmentData_spp", "mantbspp_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("mantbspp_" + str(SppNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("mantbspp_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                    SpNum = str(field.name)
                    SpNum = SpNum.strip("SCNTFC_CD")
                    SpCov = str("EST_CVR_RT" + SpNum)
                    arcpy.CalculateField_management("mantbspp_" + str(SppNum), "EST_CVR_RT", "!" + SpCov + "!", "PYTHON_9.3")
                    SppNum += 1
            sppfld = arcpy.ListFeatureClasses("mantbspp_*")
            arcpy.Append_management(sppfld, "ManualTreatmentData_spp", "NO_TEST")
            arcpy.Select_analysis("ManualTreatmentData_spp", "ManualTreatmentData_sppsel", "\"SCNTFC_CD\" IS NOT NULL")
            sppcnt = arcpy.GetCount_management("ManualTreatmentData_sppsel").getOutput(0)
            if int(sppcnt) > 0:
                arcpy.AddField_management("ManualTreatmentData_sppsel", "cvrrttx", "TEXT", "", "", 20)
                arcpy.CalculateField_management("ManualTreatmentData_sppsel", "cvrrttx", "!EST_CVR_RT!", "PYTHON_9.3") 
                add_records("Manual Species", "ManualTreatmentData_sppsel", ["SCNTFC_CD", "cvrrttx", "TRT_GUID"], "mantb_all", "TREATMENTSPECIES")            
        # Check for mechanical treatment data
        for fc in arcpy.ListFeatureClasses("MechanicalTreatmentData"):
            arcpy.AddMessage("Processing mechanical data.")
            arcpy.CopyFeatures_management("MechanicalTreatmentData", "MechanicalTreatmentData_fc")
            mechin = arcpy.GetCount_management("MechanicalTreatmentData_fc").getOutput(0)
            arcpy.AddMessage("Mechanical Data Input Count: " + str(mechin))
            arcpy.AddField_management("MechanicalTreatmentData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("MechanicalTreatmentData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)
            mechfm = arcpy.FieldMappings()
            mechfm.addTable(SDEgdb + "\\dbo.TreatmentComponentLocation")
            mechbef = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            arcpy.Append_management("MechanicalTreatmentData_fc", SDEgdb + "\\dbo.TreatmentComponentLocation", "NO_TEST", mechfm)
            mechaft = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            mechdif = int(mechaft) - int(mechbef)
            arcpy.AddMessage(str(mechdif) + " records added to TreatmentComponentLocation")
            
            # Merge to MECHANICALCOMPONENT
            arcpy.CopyFeatures_management("MechanicalTreatmentData_fc", "MechanicalTreatmentData_mechcomp")        
            arcpy.AddField_management("MechanicalTreatmentData_mechcomp", "tot_est_cvr_rt", "DOUBLE")
            arcpy.AddField_management("MechanicalTreatmentData_mechcomp", "temp_fld", "DOUBLE")
            for field in arcpy.ListFields("MechanicalTreatmentData_mechcomp", "EST_CVR_RT*"):
                arcpy.CalculateField_management("MechanicalTreatmentData_mechcomp", "temp_fld", "!" + field.name + "!", "PYTHON_9.3")
                arcpy.CalculateField_management("MechanicalTreatmentData_mechcomp", "tot_est_cvr_rt", "cvrac(!tot_est_cvr_rt!,!temp_fld!)", "PYTHON_9.3", totaccalc)
            arcpy.DeleteField_management("MechanicalTreatmentData_mechcomp", "tempfld")
            arcpy.CalculateField_management("MechanicalTreatmentData_mechcomp", "MECHCMP_ME", "!CLCACRE_ME! * !tot_est_cvr_rt! / 100", "PYTHON_9.3")
            add_records("Mechanical Species", "MechanicalTreatmentData_mechcomp", ["MECH_CL_NM", "TRT_GUID"], "mechtb2", "MECHANICALCOMPONENT")        
            # Split out SCNTFC_CD fields
            arcpy.CopyFeatures_management("MechanicalTreatmentData", "MechanicalTreatmentData_spp")
            SppNum = 1
            for field in arcpy.ListFields("MechanicalTreatmentData_spp", "SCNTFC_CD*"):
                arcpy.Select_analysis("MechanicalTreatmentData_spp", "mechtbspp_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("mechtbspp_" + str(SppNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("mechtbspp_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                    SpNum = str(field.name)
                    SpNum = SpNum.strip("SCNTFC_CD")
                    SpCov = str("EST_CVR_RT" + SpNum)
                    arcpy.CalculateField_management("mechtbspp_" + str(SppNum), "EST_CVR_RT", "!" + SpCov + "!", "PYTHON_9.3")
                    SppNum += 1
            sppfld = arcpy.ListFeatureClasses("mechtbspp_*")
            arcpy.Append_management(sppfld, "MechanicalTreatmentData_spp", "NO_TEST")
            arcpy.Select_analysis("MechanicalTreatmentData_spp", "MechanicalTreatmentData_sppsel", "\"SCNTFC_CD\" IS NOT NULL")
            sppcnt = arcpy.GetCount_management("MechanicalTreatmentData_sppsel").getOutput(0)
            if int(sppcnt) > 0:
                arcpy.AddField_management("MechanicalTreatmentData_sppsel", "cvrrttx", "TEXT", "", "", 20)
                arcpy.CalculateField_management("MechanicalTreatmentData_sppsel", "cvrrttx", "!EST_CVR_RT!", "PYTHON_9.3") 
                add_records("Mechanical Species", "MechanicalTreatmentData_sppsel", ["SCNTFC_CD", "cvrrttx", "TRT_GUID"], "mechtb_all", "TREATMENTSPECIES")            
        # Check for restoration treatment data
        for fc in arcpy.ListFeatureClasses("RestorationTreatmentData"):
            arcpy.AddMessage("Processing restoration data.")
            arcpy.CopyFeatures_management("RestorationTreatmentData", "RestorationTreatmentData_fc")
            resin = arcpy.GetCount_management("RestorationTreatmentData_fc").getOutput(0)
            arcpy.AddMessage("Restoration Data Input Count: " + str(resin))
            arcpy.AddField_management("RestorationTreatmentData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("RestorationTreatmentData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)
            resfm = arcpy.FieldMappings()
            resfm.addTable(SDEgdb + "\\dbo.TreatmentComponentLocation")
            resbef = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            arcpy.Append_management("RestorationTreatmentData_fc", SDEgdb + "\\dbo.TreatmentComponentLocation", "NO_TEST", resfm)
            resaft = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            resdif = int(resaft) - int(resbef)
            arcpy.AddMessage(str(resdif) + " records added to TreatmentComponentLocation")
            
            # Merge to RESTORATIONCOMPONENT
            arcpy.CopyFeatures_management("RestorationTreatmentData_fc", "RestorationTreatmentData_rescomp")
            ResNum = 1
            for field in arcpy.ListFields("RestorationTreatmentData_rescomp", "REST_CL_NM*"):
                arcpy.Select_analysis("RestorationTreatmentData_rescomp", "restb_" + str(ResNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("restb_" + str(ResNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("restb_" + str(ResNum), "REST_CL_NM", "!" + field.name + "!", "PYTHON_9.3")
            resfld = arcpy.ListFeatureClasses("restb_*")
            arcpy.Append_management(resfld, "RestorationTreatmentData_rescomp", "NO_TEST")
            arcpy.Select_analysis("RestorationTreatmentData_rescomp", "RestorationTreatmentData_rescompsel", "\"REST_CL_NM\" IS NOT NULL")
            rescnt = arcpy.GetCount_management("RestorationTreatmentData_rescompsel").getOutput(0)
            add_records("Restoration Component", "RestorationTreatmentData_rescompsel", ["REST_CL_NM", "TRT_GUID"], "restb2", "RESTORATIONCOMPONENT")        
            # Split out SCNTFC_CD fields
            arcpy.CopyFeatures_management("RestorationTreatmentData", "RestorationTreatmentData_spp")
            SppNum = 1
            for field in arcpy.ListFields("RestorationTreatmentData_spp", "SCNTFC_CD*"):
                arcpy.Select_analysis("RestorationTreatmentData_spp", "restbspp_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("restbspp_" + str(SppNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("restbspp_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                    SpNum = str(field.name)
                    SpNum = SpNum.strip("SCNTFC_CD")
                    SpCov = str("EST_CVR_RT" + SpNum)
                    arcpy.CalculateField_management("restbspp_" + str(SppNum), "EST_CVR_RT", "!" + SpCov + "!", "PYTHON_9.3")
                    SppNum += 1
            sppfld = arcpy.ListFeatureClasses("restbspp_*")
            arcpy.Append_management(sppfld, "RestorationTreatmentData_spp", "NO_TEST")
            arcpy.Select_analysis("RestorationTreatmentData_spp", "RestorationTreatmentData_sppsel", "\"SCNTFC_CD\" IS NOT NULL")
            sppcnt = arcpy.GetCount_management("RestorationTreatmentData_sppsel").getOutput(0)
            if int(sppcnt) > 0:
                arcpy.AddField_management("RestorationTreatmentData_sppsel", "cvrrttx", "TEXT", "", "", 20)
                arcpy.CalculateField_management("RestorationTreatmentData_sppsel", "cvrrttx", "!EST_CVR_RT!", "PYTHON_9.3")
                add_records("Restoration Species", "RestorationTreatmentData_sppsel", ["SCNTFC_CD", "cvrrttx", "TRT_GUID"], "restb_all", "TREATMENTSPECIES")
        # Check for revegetation treatment data
        for fc in arcpy.ListFeatureClasses("RevegetationTreatmentData"):
            arcpy.AddMessage("Processing revegetation data.")
            arcpy.CopyFeatures_management("RevegetationTreatmentData", "RevegetationTreatmentData_fc")
            revin = arcpy.GetCount_management("RevegetationTreatmentData_fc").getOutput(0)
            arcpy.AddMessage("Revegetation Data Input Count: " + str(revin))
            arcpy.AddField_management("RevegetationTreatmentData_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("RevegetationTreatmentData_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)
            revfm = arcpy.FieldMappings()
            revfm.addTable(SDEgdb + "\\dbo.TreatmentComponentLocation")
            revbef = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            arcpy.Append_management("RevegetationTreatmentData_fc", SDEgdb + "\\dbo.TreatmentComponentLocation", "NO_TEST", revfm)
            revaft = arcpy.GetCount_management(SDEgdb + "\\dbo.TreatmentComponentLocation").getOutput(0)
            revdif = int(revaft) - int(revbef)
            arcpy.AddMessage(str(revdif) + " records added to TreatmentComponentLocation")
            
            # Merge to REVEGETATIONCOMPONENT
            arcpy.CopyFeatures_management("RevegetationTreatmentData_fc", "RevegetationTreatmentData_revcomp")
            add_records("Revegetation Component", "RevegetationTreatmentData_revcomp", ["VEG_UOM_NM", "PHNLGY_NM", "STOCK_ME", "TRT_GUID"], "revtb2", "REVEGETATIONCOMPONENT")        
            # Split out SCNTFC_CD fields
            arcpy.CopyFeatures_management("RevegetationTreatmentData", "RevegetationTreatmentData_spp")
            SppNum = 1
            for field in arcpy.ListFields("RevegetationTreatmentData_spp", "SCNTFC_CD*"):
                arcpy.Select_analysis("RevegetationTreatmentData_spp", "revtbspp_" + str(SppNum), "\"" + field.name + "\"" + " IS NOT NULL")
                RecNum = arcpy.GetCount_management("revtbspp_" + str(SppNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("revtbspp_" + str(SppNum), "SCNTFC_CD", "!" + field.name + "!", "PYTHON_9.3")
                    SpNum = str(field.name)
                    SpNum = SpNum.strip("SCNTFC_CD")
                    SpCov = str("EST_CVR_RT" + SpNum)
                    arcpy.CalculateField_management("revtbspp_" + str(SppNum), "EST_CVR_RT", "!" + SpCov + "!", "PYTHON_9.3")
                    SppNum += 1
            sppfld = arcpy.ListFeatureClasses("revtbspp_*")
            arcpy.Append_management(sppfld, "RevegetationTreatmentData_spp", "NO_TEST")
            arcpy.Select_analysis("RevegetationTreatmentData_spp", "RevegetationTreatmentData_sppsel", "\"SCNTFC_CD\" IS NOT NULL")
            sppcnt = arcpy.GetCount_management("RevegetationTreatmentData_sppsel").getOutput(0)
            if int(sppcnt) > 0:
                arcpy.AddField_management("RevegetationTreatmentData_sppsel", "cvrrttx", "TEXT", "", "", 20)
                arcpy.CalculateField_management("RevegetationTreatmentData_sppsel", "cvrrttx", "!EST_CVR_RT!", "PYTHON_9.3")
                add_records("Revegetation Species", "RevegetationTreatmentData_sppsel", ["SCNTFC_CD", "cvrrttx", "TRT_GUID"], "revtb_all", "TREATMENTSPECIES")            

        # Check for photo location data
        for fc in arcpy.ListFeatureClasses("PhotoLocation"):
            arcpy.AddMessage("Processing photo location data.")
            arcpy.CopyFeatures_management("PhotoLocation", "PhotoLocation_fc")
            photlocin = arcpy.GetCount_management("PhotoLocation_fc").getOutput(0)
            arcpy.AddMessage("Photo Location Input Count: " + str(photlocin))
            arcpy.AddField_management("PhotoLocation_fc", "UPLOAD_DT", "DATE")
            arcpy.CalculateField_management("PhotoLocation_fc", "UPLOAD_DT", "add_date()", "PYTHON_9.3", today_cb)
            photfm = arcpy.FieldMappings()
            photfm.addTable(SDEgdb + "\\dbo.PhotoLocation")
            photlocbef = arcpy.GetCount_management(SDEgdb + "\\dbo.PhotoLocation").getOutput(0)
            arcpy.Append_management("PhotoLocation_fc", SDEgdb + "\\dbo.PhotoLocation", "NO_TEST", photfm)
            photlocaft = arcpy.GetCount_management(SDEgdb + "\\dbo.PhotoLocation").getOutput(0)
            photlocdif = int(photlocaft) - int(photlocbef)
            arcpy.AddMessage(str(photlocdif) + " records added to PhotoLocation")
            
            # Split out PHOTOS
            arcpy.CopyFeatures_management("PhotoLocation", "PhotoLocation_photos")
            PhNum = 1
            for field in arcpy.ListFields("PhotoLocation_photos", "PHOTODATE*"):
                arcpy.Select_analysis("PhotoLocation_photos", "Phototb_" + str(PhNum), "\"" + field.name + "\" IS NOT NULL")
                RecNum = arcpy.GetCount_management("Phototb_" + str(PhNum)).getOutput(0)
                if int(RecNum) > 0:
                    arcpy.CalculateField_management("Phototb_" + str(PhNum), "PHOTODATE", "!" + field.name + "!", "PYTHON_9.3")
                    PhNR = str(field.name)
                    PhNR = PhNR.strip("PHOTODATE")
                    PhDeg = str("PHOTODEG" + PhNR)
                    arcpy.CalculateField_management("Phototb_" + str(PhNum), "PHOTODEG", "!" + PhDeg + "!", "PYTHON_9.3")
                    PhPre = str("PREFIX" + PhNR)
                    arcpy.CalculateField_management("Phototb_" + str(PhNum), "PREFIX", "!" + PhPre + "!", "PYTHON_9.3")
                    PhPNr = str("PHOTONUM" + PhNR)
                    arcpy.CalculateField_management("Phototb_" + str(PhNum), "PHOTONUM", "!" + PhPNr + "!", "PYTHON_9.3")
                    PhPur = str("PURPOSE" + PhNR)
                    arcpy.CalculateField_management("Phototb_" + str(PhNum), "PURPOSE", "!" + PhPur + "!", "PYTHON_9.3")
                    PhPh = str("PHOTO" + PhNR)
                    arcpy.CalculateField_management("Phototb_" + str(PhNum), "PHOTO", "!" + PhPh + "!", "PYTHON_9.3")
                    PhNum += 1
            arcpy.CreateFeatureclass_management("memory", "PhotoLocation_photos2", "POINT", "PhotoLocation_photos", "", "", new_spatialref)
            phfld = arcpy.ListFeatureClasses("Phototb_*")
            arcpy.Append_management(phfld, "PhotoLocation_photos2", "NO_TEST")
            arcpy.Select_analysis("PhotoLocation_photos2", "PhotoLocation_photos2sel", "\"PHOTODATE\" IS NOT NULL")
            phcnt = arcpy.GetCount_management("PhotoLocation_photos2sel").getOutput(0)
            if int(phcnt) > 0:
                arcpy.CopyRows_management("PhotoLocation_photos2sel", "pht_all")
                arcpy.AddMessage("Photo Input Count: " + str(phcnt))
                phottbfm = arcpy.FieldMappings()
                phottbfm.addTable(SDEgdb + "\\dbo.PHOTOS")
                photbef = arcpy.GetCount_management(SDEgdb + "\\dbo.PHOTOS").getOutput(0)
                arcpy.Append_management("pht_all", SDEgdb + "\\dbo.PHOTOS", "NO_TEST", phottbfm)                    
                photaft = arcpy.GetCount_management(SDEgdb + "\\dbo.PHOTOS").getOutput(0)
                photdif = int(photaft) - int(photbef)
                arcpy.AddMessage(str(photdif) + " records added to PHOTOS")
            
    # except Exception as e:

    #     tb = sys.exc_info()[2]
    #     tbinfo = traceback.format_tb(tb)[0]
    #     pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n      " + str(sys.exc_info()[1])
    #     msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"
    #     arcpy.AddError(e)
    #     arcpy.AddError(msgs)
    #     arcpy.AddError(pymsg)

    finally:
        arcpy.Delete_management("memory")


if __name__ == '__main__':
    # Input variables
    QCgdb = arcpy.GetParameterAsText(0)
    SDEgdb = arcpy.GetParameterAsText(1)

    # Define variables
    today_cb = """def add_date():
        return time.strftime(\"%Y/%m/%d %H:%M:%S\")"""
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
    curnull = """def calccur(newcd, oldcur):
        if newcd == \"H\":
            return newcd
        else:
            return oldcur"""
    send_cb = """def Calc(minenddt):
        if minenddt is None:
            return \"C\"
        else:
            return \"H\""""        
    endnotnull_cb = """def Calc(curcd, enddt1, enddt2):
        if curcd == \"H\":
            if enddt1 is None:
                return enddt2
            else:
                return enddt1
        else:
            return"""
    null_cb = """def calcnull(curcd):
        if curcd is None:
            return \"C\"
        else:
            return curcd"""
    totaccalc = """def cvrac(totcvr, newcvr):
        if newcvr is None:
            return totcvr
        else:
            if totcvr is None:
                totcvr = 0
            newtotcvr = totcvr + newcvr
            return newtotcvr"""

    main()
