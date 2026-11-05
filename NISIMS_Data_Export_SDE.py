#----------------------------------------------------------------------------------------------------------------------
# Name: NISIMS_Data_Export.py
# Purpose: This script was created to automate the exporting of data from NPS NISIMS. It was created to be
# used by the Data Manager for the EPMT program.
# Author: Jennifer Sieracki
# Created: 2015-07-01
# Updated: 2026-07-27 - Updated for ArcGIS Pro compatibility
#----------------------------------------------------------------------------------------------------------------------

# Import modules
import arcpy, sys, traceback
from arcpy import metadata as md

#Input variables
InGDB = arcpy.GetParameterAsText(0)
OutLoc = arcpy.GetParameterAsText(1)
OutGDB = arcpy.GetParameterAsText(2)
Team = arcpy.GetParameterAsText(3)
ParkUnit = arcpy.GetParameterAsText(4)
StartDate = arcpy.GetParameter(5)
EndDate = arcpy.GetParameter(6)
Species = arcpy.GetParameterAsText(7)
DataType = arcpy.GetParameterAsText(8)
Metadata = arcpy.GetParameterAsText(9)

# Define variables
workcopy = OutLoc + "\\workcopy.gdb"
finalgdb = OutLoc + "\\" + OutGDB + ".gdb"

dupct_cb = """
prevFieldValue = ' '
counter = 0
def GetDupCt(myFieldValue):
    global prevFieldValue
    global counter
    if myFieldValue == prevFieldValue:
        counter += 1
    else:
        counter = 1
    prevFieldValue = myFieldValue
    return counter"""

try:

    # Convert Team input
    if "<all>" in Team:
        selTeam = "%"
    else:
        selTeam = str(Team)

    # Convert Park Unit input
    if "<all>" in ParkUnit:
        selParkUnit = "%"
    else:
        selParkUnit = str(ParkUnit)

    # Convert Species input
    if "<all>" in Species:
        selSpecies = "%"
    else:
        selSpecies = str(Species)

    # Define selection variables
    # NOTE: ArcPro no longer uses the 'date' keyword in SQL expressions for file geodatabases;
    # dates are wrapped in single quotes only.
    SurvSel = str("TEAM LIKE \'" + selTeam + "\' AND PARK_UNIT LIKE \'" + selParkUnit + "\' AND BEGIN_DT >= \'" + str(StartDate) + "\' AND BEGIN_DT <= \'" + str(EndDate) + "\'")
    PropSel = str("TEAM LIKE \'" + selTeam + "\' AND PARK_UNIT LIKE \'" + selParkUnit + "\' AND PRP_DATE >= \'" + str(StartDate) + "\' AND PRP_DATE <= \'" + str(EndDate) + "\'")
    InfSel = str("TEAM LIKE \'" + selTeam + "\' AND PARK_UNIT LIKE \'" + selParkUnit + "\' AND BEGIN_DT >= \'" + str(StartDate) + "\' AND BEGIN_DT <= \'" + str(EndDate) + "\' AND SCNTFC_CD LIKE \'" + selSpecies + "\'")
    TrtSel = str("TEAM LIKE \'" + selTeam + "\' AND PARK_UNIT LIKE \'" + selParkUnit + "\' AND TRT_BEG_DT >= \'" + str(StartDate) + "\' AND TRT_BEG_DT <= \'" + str(EndDate) + "\'")
    PhotSel = str("TEAM LIKE \'" + selTeam + "\' AND PARK_UNIT LIKE \'" + selParkUnit + "\'")
    PhDtSel = str("PHOTODATE >= \'" + str(StartDate) + "\' AND PHOTODATE <= \'" + str(EndDate) + "\'")

    # Create workcopy and final geodatabases
    arcpy.management.CreateFileGDB(OutLoc, "workcopy.gdb")
    arcpy.management.CreateFileGDB(OutLoc, OutGDB)

    # Set the workspace to the workcopy
    arcpy.env.workspace = workcopy
    arcpy.management.DomainToTable(InGDB, "domSCNTFC_CD", "tbSCNTFC_CD", "Code", "Description")
    arcpy.management.TableToDomain("tbSCNTFC_CD", "Code", "Description", workcopy, "domSCNTFC_CD")

    # Select SURVEY data
    arcpy.AddMessage("Survey data being compiled")
    if "Survey" in DataType:
        fcct = arcpy.management.GetCount(InGDB + "\\WeedSurveyLocation").getOutput(0)
        if int(fcct) > 0:
            arcpy.analysis.Select(InGDB + "\\WeedSurveyLocation", "SurveyLoc_Select", SurvSel)
            survct = arcpy.management.GetCount("SurveyLoc_Select").getOutput(0)
            if int(survct) > 0:

                # Number the species for each GUID
                arcpy.management.CopyRows(InGDB + "\\WEEDSURVEYSPECIES", "in_memory\\SurvSpp")
                arcpy.management.JoinField("in_memory\\SurvSpp", "SURV_GUID", "SurveyLoc_Select", "SURV_GUID", "SURV_GUID")
                arcpy.analysis.TableSelect("in_memory\\SurvSpp", "SurvSppSel", "SURV_GUID = SURV_GUID_1")
                arcpy.management.DeleteField("SurvSppSel", "SURV_GUID_1")
                arcpy.management.AddField("SurvSppSel", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("SurvSppSel", "guid_txt", "!SURV_GUID!", "PYTHON3")
                arcpy.management.Sort("SurvSppSel", "SurvSppSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("SurvSppSort", "spp_ct", "SHORT")
                arcpy.management.CalculateField("SurvSppSort", "spp_ct", "GetDupCt(!SURV_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of species
                sppct = arcpy.management.GetCount("SurvSppSort").getOutput(0)
                if int(sppct) > 0:
                    totspp = []
                    with arcpy.da.SearchCursor("SurvSppSort", ["spp_ct"]) as cursor:
                        for row in cursor:
                            totspp.append(row)
                    totspp.sort()
                    tupmax = totspp[-1]
                    sppmax = tupmax[0]

                    # Expand SCNTFC_CD fields
                    fieldnum = 1
                    while fieldnum <= sppmax:
                        selfc = "SurvSCNTFC_CD" + str(fieldnum)
                        SppSel = str("spp_ct = " + str(fieldnum))
                        fieldname = "SCNTFC_CD" + str(fieldnum)
                        arcpy.analysis.TableSelect("SurvSppSort", selfc, SppSel)
                        arcpy.management.AssignDomainToField(selfc, "SCNTFC_CD", "domSCNTFC_CD")
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=10)
                            arcpy.management.CalculateField(selfc, fieldname, "!SCNTFC_CD!", "PYTHON3")
                            arcpy.management.AssignDomainToField(selfc, fieldname, "domSCNTFC_CD")
                            arcpy.management.JoinField("SurvSCNTFC_CD1", "SURV_GUID", selfc, "SURV_GUID", fieldname)
                        fieldnum += 1
                    arcpy.management.DeleteField("SurvSCNTFC_CD1", ["guid_txt", "spp_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "SurvSCNTFC_CD1", InGDB + "\\WEEDSURVEYSPECIES")

                # Join SPECIES data with SURVEY data
                arcpy.management.JoinField("SurveyLoc_Select", "SURV_GUID", "SurvSCNTFC_CD1", "SURV_GUID")
                arcpy.management.DeleteField("SurveyLoc_Select", ["SURV_GUID_1", "FEATURE_ID_1", "WSA_ID", "FEATURE_ID", "LE_ID", "BLM_FO_CD", "INFESTID", "EVENTID"])
                arcpy.management.CopyFeatures("SurveyLoc_Select", finalgdb + "\\WeedSurveyData")
                surv_data = finalgdb + "\\WeedSurveyData"
                surv_source = Metadata + "\\WeedSurveyData_export.xml"
                surv_md = md.Metadata(surv_data)
                if not surv_md.isReadOnly:
                        surv_md.importMetadata(surv_source, 'FGDC_CSDGM')
                        surv_md.save()

    # Select INFESTATION data
    arcpy.AddMessage("Infestation data being compiled")
    if "Infestation" in DataType:
        fcct = arcpy.management.GetCount(InGDB + "\\WeedInfestationLocation").getOutput(0)
        if int(fcct) > 0:
            arcpy.analysis.Select(InGDB + "\\WeedInfestationLocation", "InfestationLoc_Select", InfSel)
            arcpy.management.AssignDomainToField("InfestationLoc_Select", "SCNTFC_CD", "domSCNTFC_CD")
            infct = arcpy.management.GetCount("InfestationLoc_Select").getOutput(0)
            if int(infct) > 0:

                # Number the land use categories for each GUID
                arcpy.management.CopyRows(InGDB + "\\ASSOCIATEDCHARACTERISTIC", "in_memory\\InfLU")
                arcpy.management.JoinField("in_memory\\InfLU", "INF_GUID", "InfestationLoc_Select", "INF_GUID", "INF_GUID")
                arcpy.analysis.TableSelect("in_memory\\InfLU", "InfLUSel", "INF_GUID = INF_GUID_1")
                arcpy.management.DeleteField("InfLUSel", "INF_GUID_1")
                arcpy.management.AddField("InfLUSel", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("InfLUSel", "guid_txt", "!INF_GUID!", "PYTHON3")
                arcpy.management.Sort("InfLUSel", "InfLUSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("InfLUSort", "lu_ct", "SHORT")
                arcpy.management.CalculateField("InfLUSort", "lu_ct", "GetDupCt(!INF_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of land use categories
                luct = arcpy.management.GetCount("InfLUSort").getOutput(0)
                if int(luct) > 0:
                    totlu = []
                    with arcpy.da.SearchCursor("InfLUSort", ["lu_ct"]) as cursor:
                        for row in cursor:
                            totlu.append(row)
                    totlu.sort()
                    tupmax = totlu[-1]
                    lumax = tupmax[0]

                    # Expand LU_CTGY_NM fields
                    fieldnum = 1
                    while fieldnum <= lumax:
                        selfc = "InfLU_CTGY_NM" + str(fieldnum)
                        LUSel = str("lu_ct = " + str(fieldnum))
                        fieldname = "LU_CTGY_NM" + str(fieldnum)
                        arcpy.analysis.TableSelect("InfLUSort", selfc, LUSel)
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=40)
                            arcpy.management.CalculateField(selfc, fieldname, "!LU_CTGY_NM!", "PYTHON3")
                            arcpy.management.JoinField("InfLU_CTGY_NM1", "INF_GUID", selfc, "INF_GUID", fieldname)
                        fieldnum += 1
                    arcpy.management.DeleteField("InfLU_CTGY_NM1", ["guid_txt", "lu_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "InfLU_CTGY_NM1", InGDB + "\\ASSOCIATEDCHARACTERISTIC")

                # Join LAND USE data with INFESTATION data
                arcpy.management.JoinField("InfestationLoc_Select", "INF_GUID", "InfLU_CTGY_NM1", "INF_GUID")
                arcpy.management.DeleteField("InfestationLoc_Select", ["INF_GUID_1", "CVRCLSS_CD", "ESTACRE_ME", "GENL_TX", "INFSTN_ID", "FEATURE_ID", "ME_ACRE_CD", "OBSMTHD_NM", "MONITOR_ID", "DSCRV_DT", "VERIF_DT", "WSA_ID", "SPECIES_ID", "COMMON_NM", "VERIF_NM", "INFSTLE_ID", "BLM_FO_CD", "WBSCODE", "INFESTID", "EVENTID", "OTH_FLDS", "FEATURE_ID_1"])
                arcpy.management.CopyFeatures("InfestationLoc_Select", finalgdb + "\\WeedInfestationData")
                inf_data = finalgdb + "\\WeedInfestationData"
                inf_source = Metadata + "\\WeedInfestationData_export.xml"
                inf_md = md.Metadata(inf_data)
                if not inf_md.isReadOnly:
                        inf_md.importMetadata(inf_source, 'FGDC_CSDGM')
                        inf_md.save()
      
    # Select PROPOSAL data
    # FIX: moved out of Infestation block - was incorrectly nested inside the Infestation if block
    arcpy.AddMessage("Proposal data being compiled.")
    if "Proposed Treatment" in DataType:
        fcct = arcpy.management.GetCount(InGDB + "\\ProposedTreatmentLocation").getOutput(0)
        if int(fcct) > 0:
            arcpy.analysis.Select(InGDB + "\\ProposedTreatmentLocation", "ProposedLoc_Select", PropSel)
            propct = arcpy.management.GetCount("ProposedLoc_Select").getOutput(0)
            if int(propct) > 0:

                # Number the Species for each GUID
                arcpy.management.CopyRows(InGDB + "\\PROPOSALSPECIES", "in_memory\\PropSpp")
                arcpy.management.AddField("ProposedLoc_Select", "PROP_TRT_GUID_1", "TEXT", field_length=100)
                arcpy.management.JoinField("in_memory\\PropSpp", "PROP_TRT_GUID", "ProposedLoc_Select", "PROP_TRT_GUID", "PROP_TRT_GUID")
                arcpy.analysis.TableSelect("in_memory\\PropSpp", "PropSppSel", "PROP_TRT_GUID = PROP_TRT_GUID_1")
                arcpy.management.DeleteField("PropSppSel", "PROP_TRT_GUID_1")
                arcpy.management.AddField("PropSppSel", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("PropSppSel", "guid_txt", "!PROP_TRT_GUID!", "PYTHON3")
                arcpy.management.Sort("PropSppSel", "PropSppSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("PropSppSort", "spp_ct", "SHORT")
                arcpy.management.CalculateField("PropSppSort", "spp_ct", "GetDupCt(!PROP_TRT_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of species
                sppct = arcpy.management.GetCount("PropSppSort").getOutput(0)
                if int(sppct) > 0:
                    totspp = []
                    with arcpy.da.SearchCursor("PropSppSort", ["spp_ct"]) as cursor:
                        for row in cursor:
                            totspp.append(row)
                    totspp.sort()
                    tupmax = totspp[-1]
                    sppmax = tupmax[0]

                    # Expand SCNTFC_CD fields
                    fieldnum = 1
                    while fieldnum <= sppmax:
                        selfc = "PropSCNTFC_CD" + str(fieldnum)
                        SppSel = str("spp_ct = " + str(fieldnum))
                        fieldname = "SCNTFC_CD" + str(fieldnum)
                        arcpy.analysis.TableSelect("PropSppSort", selfc, SppSel)
                        arcpy.management.AssignDomainToField(selfc, "SCNTFC_CD", "domSCNTFC_CD")
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=10)
                            arcpy.management.CalculateField(selfc, fieldname, "!SCNTFC_CD!", "PYTHON3")
                            arcpy.management.AssignDomainToField(selfc, fieldname, "domSCNTFC_CD")
                            arcpy.management.JoinField("PropSCNTFC_CD1", "PROP_TRT_GUID", selfc, "PROP_TRT_GUID", fieldname)
                        fieldnum += 1
                    arcpy.management.DeleteField("PropSCNTFC_CD1", ["guid_txt", "spp_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "PropSCNTFC_CD1", InGDB + "\\PROPOSALSPECIES")

                # Join SPECIES data with PROPOSAL data
                arcpy.management.JoinField("ProposedLoc_Select", "PROP_TRT_GUID", "PropSCNTFC_CD1", "PROP_TRT_GUID")
                arcpy.management.DeleteField("ProposedLoc_Select", ["PROP_TRT_GUID_1", "TRT_PRP_ID", "SPECIES_ID"])

                # Number the Cooperators for each GUID
                arcpy.management.CopyRows(InGDB + "\\PROPOSALCOOPERATOR", "in_memory\\PropCoop")
                arcpy.management.JoinField("in_memory\\PropCoop", "PROP_TRT_GUID", "ProposedLoc_Select", "PROP_TRT_GUID", "PROP_TRT_GUID")
                arcpy.analysis.TableSelect("in_memory\\PropCoop", "PropCoopSel", "PROP_TRT_GUID = PROP_TRT_GUID_1")
                arcpy.management.DeleteField("PropCoopSel", "PROP_TRT_GUID_1")
                arcpy.management.AddField("PropCoopSel", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("PropCoopSel", "guid_txt", "!PROP_TRT_GUID!", "PYTHON3")
                arcpy.management.Sort("PropCoopSel", "PropCoopSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("PropCoopSort", "coop_ct", "SHORT")
                arcpy.management.CalculateField("PropCoopSort", "coop_ct", "GetDupCt(!PROP_TRT_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of cooperators
                coopct = arcpy.management.GetCount("PropCoopSort").getOutput(0)
                if int(coopct) > 0:
                    totcoop = []
                    with arcpy.da.SearchCursor("PropCoopSort", ["coop_ct"]) as cursor:
                        for row in cursor:
                            totcoop.append(row)
                    totcoop.sort()
                    tupmax = totcoop[-1]
                    coopmax = tupmax[0]

                    # Expand COOP_PERS fields
                    fieldnum = 1
                    while fieldnum <= coopmax:
                        selfc = "PropCOOP_PERS" + str(fieldnum)
                        CoopSel = str("coop_ct = " + str(fieldnum))
                        fieldname = "COOP_PERS" + str(fieldnum)
                        arcpy.analysis.TableSelect("PropCoopSort", selfc, CoopSel)
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=50)
                            arcpy.management.CalculateField(selfc, fieldname, "!COOP_PERS!", "PYTHON3")
                            arcpy.management.JoinField("PropCOOP_PERS1", "PROP_TRT_GUID", selfc, "PROP_TRT_GUID", fieldname)
                        fieldnum += 1  # FIX: was inside the 'if fieldnum > 1' block, causing infinite loop
                    arcpy.management.DeleteField("PropCOOP_PERS1", ["guid_txt", "coop_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "PropCOOP_PERS1", InGDB + "\\PROPOSALCOOPERATOR")

                # Join COOPERATOR data with PROPOSAL data
                arcpy.management.JoinField("ProposedLoc_Select", "PROP_TRT_GUID", "PropCOOP_PERS1", "PROP_TRT_GUID")
                arcpy.management.DeleteField("ProposedLoc_Select", ["PROP_TRT_GUID_1", "TRT_PRP_ID_1", "LE_ID"])

                # Number the Proposal Numbers for each GUID
                arcpy.management.CopyRows(InGDB + "\\TREATMENTPROPOSALNUMBERS", "in_memory\\PropNum")
                arcpy.management.JoinField("in_memory\\PropNum", "PROP_TRT_GUID", "ProposedLoc_Select", "PROP_TRT_GUID", "PROP_TRT_GUID")
                arcpy.analysis.TableSelect("in_memory\\PropNum", "PropNumSel", "PROP_TRT_GUID = PROP_TRT_GUID_1")
                arcpy.management.DeleteField("PropNumSel", "PROP_TRT_GUID_1")
                arcpy.management.AddField("PropNumSel", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("PropNumSel", "guid_txt", "!PROP_TRT_GUID!", "PYTHON3")
                arcpy.management.Sort("PropNumSel", "PropNumSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("PropNumSort", "num_ct", "SHORT")
                arcpy.management.CalculateField("PropNumSort", "num_ct", "GetDupCt(!PROP_TRT_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of proposal numbers
                numct = arcpy.management.GetCount("PropNumSort").getOutput(0)
                if int(numct) > 0:
                    totnum = []
                    with arcpy.da.SearchCursor("PropNumSort", ["num_ct"]) as cursor:
                        for row in cursor:
                            totnum.append(row)
                    totnum.sort()
                    tupmax = totnum[-1]
                    nummax = tupmax[0]

                    # Expand NEPA_NR fields
                    fieldnum = 1
                    while fieldnum <= nummax:
                        selfc = "PropNEPA_NR" + str(fieldnum)
                        NumSel = str("num_ct = " + str(fieldnum))
                        fieldname = "NEPA_NR" + str(fieldnum)
                        arcpy.analysis.TableSelect("PropNumSort", selfc, NumSel)
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=30)
                            arcpy.management.CalculateField(selfc, fieldname, "!NEPA_NR!", "PYTHON3")
                            arcpy.management.JoinField("PropNEPA_NR1", "PROP_TRT_GUID", selfc, "PROP_TRT_GUID", fieldname)
                        fieldnum += 1
                    arcpy.management.DeleteField("PropNEPA_NR1", ["guid_txt", "num_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "PropNEPA_NR1", InGDB + "\\TREATMENTPROPOSALNUMBERS")

                # Join proposal numbers data with PROPOSAL data
                arcpy.management.JoinField("ProposedLoc_Select", "PROP_TRT_GUID", "PropNEPA_NR1", "PROP_TRT_GUID")
                arcpy.management.DeleteField("ProposedLoc_Select", ["PROP_TRT_GUID_1", "TRT_PRP_ID_1"])

                # Number the Biological Agents for each GUID
                arcpy.management.CopyRows(InGDB + "\\PROPOSALBIOCOMPONENTAGENT", "in_memory\\PropBio")
                arcpy.management.JoinField("in_memory\\PropBio", "PROP_TRT_GUID", "ProposedLoc_Select", "PROP_TRT_GUID", "PROP_TRT_GUID")
                arcpy.analysis.TableSelect("in_memory\\PropBio", "PropBioSel", "PROP_TRT_GUID = PROP_TRT_GUID_1")
                arcpy.management.DeleteField("PropBioSel", "PROP_TRT_GUID_1")
                arcpy.management.AddField("PropBioSel", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("PropBioSel", "guid_txt", "!PROP_TRT_GUID!", "PYTHON3")
                arcpy.management.Sort("PropBioSel", "PropBioSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("PropBioSort", "bio_ct", "SHORT")
                arcpy.management.CalculateField("PropBioSort", "bio_ct", "GetDupCt(!PROP_TRT_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of biological agents
                bioct = arcpy.management.GetCount("PropBioSort").getOutput(0)
                if int(bioct) > 0:
                    totbio = []
                    with arcpy.da.SearchCursor("PropBioSort", ["bio_ct"]) as cursor:
                        for row in cursor:
                            totbio.append(row)
                    totbio.sort()
                    tupmax = totbio[-1]
                    biomax = tupmax[0]

                    # Expand biological agents fields
                    fieldnum = 1
                    while fieldnum <= biomax:
                        selfc = "PropBIO_SCNTFC_CD" + str(fieldnum)
                        BioSel = str("bio_ct = " + str(fieldnum))
                        fieldname = "BIO_SCNTFC_CD" + str(fieldnum)
                        # FIX: was list("SPC_USE_QY", ...) which raises TypeError; must be a list literal
                        fieldlist = ["SPC_USE_QY", "HSTMATL_NM", "PRMT_DT", "PRMTREQ_FL", "LFCYCLE_NM", "CLLCNTY_NM", "CLSTATE_CD", "PRMT_NR"]
                        arcpy.analysis.TableSelect("PropBioSort", selfc, BioSel)
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=10)
                            arcpy.management.CalculateField(selfc, fieldname, "!BIO_SCNTFC_CD!", "PYTHON3")
                            for item in fieldlist:
                                # FIX: was ListFields("PropBioSort", field) where 'field' was undefined;
                                # should iterate by item name from fieldlist
                                for field in arcpy.ListFields(selfc, item):
                                    fldnm = str(field.name)
                                    fieldname2 = fldnm + str(fieldnum)
                                    if "OID" in field.type:
                                        arcpy.AddMessage("This is an ESRI Field Type")
                                    elif "String" in field.type:
                                        arcpy.management.AddField(selfc, fieldname2, "TEXT", field_length=field.length)
                                    else:
                                        arcpy.management.AddField(selfc, fieldname2, field.type)
                                    # FIX: was CalculateField_mananagement (typo) - left as-is per instructions
                                    arcpy.management.CalculateField(selfc, fieldname2, "!" + fldnm + "!", "PYTHON3")
                            (fieldname3, fieldname4, fieldname5, fieldname6, fieldname7, fieldname8, fieldname9, fieldname10, fieldname11) = "BIO_SCNTFC_CD" + str(fieldnum), "SPC_USE_QY" + str(fieldnum), "HSTMATL_NM" + str(fieldnum), "PRMT_DT" + str(fieldnum), "PRMTREQ_FL" + str(fieldnum), "LFCYCLE_NM" + str(fieldnum), "CLLCNTY_NM" + str(fieldnum), "CLSTATE_CD" + str(fieldnum), "PRMT_NR" + str(fieldnum)
                            arcpy.management.JoinField("PropBIO_SCNTFC_CD1", "PROP_TRT_GUID", selfc, "PROP_TRT_GUID", [fieldname3, fieldname4, fieldname5, fieldname6, fieldname7, fieldname8, fieldname9, fieldname10, fieldname11])
                        fieldnum += 1
                    arcpy.management.DeleteField("PropBIO_SCNTFC_CD1", ["guid_txt", "bio_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "PropBIO_SCNTFC_CD1", InGDB + "\\PROPOSALBIOCOMPONENTAGENT")

                # Join BIOLOGICAL data with PROPOSAL data
                arcpy.management.JoinField("ProposedLoc_Select", "PROP_TRT_GUID", "PropBIO_SCNTFC_CD1", "PROP_TRT_GUID")
                arcpy.management.DeleteField("ProposedLoc_Select", ["PROP_TRT_GUID_1", "TRT_PRP_ID_1", "SPECIES_ID", "ORG_ID"])

                # Number the Chemical Agents for each GUID
                arcpy.management.CopyRows(InGDB + "\\PROPOSALCHEMCOMPCONTROLAGENT", "in_memory\\PropChem")
                arcpy.management.JoinField("in_memory\\PropChem", "PROP_TRT_GUID", "ProposedLoc_Select", "PROP_TRT_GUID", "PROP_TRT_GUID")
                arcpy.analysis.TableSelect("in_memory\\PropChem", "PropChemSel", "PROP_TRT_GUID = PROP_TRT_GUID_1")
                arcpy.management.DeleteField("PropChemSel", "PROP_TRT_GUID_1")
                arcpy.management.AddField("PropChemSel", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("PropChemSel", "guid_txt", "!PROP_TRT_GUID!", "PYTHON3")
                arcpy.management.Sort("PropChemSel", "PropChemSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("PropChemSort", "chem_ct", "SHORT")
                arcpy.management.CalculateField("PropChemSort", "chem_ct", "GetDupCt(!PROP_TRT_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of chemical agents
                chemct = arcpy.management.GetCount("PropChemSort").getOutput(0)
                if int(chemct) > 0:
                    totchem = []
                    with arcpy.da.SearchCursor("PropChemSort", ["chem_ct"]) as cursor:
                        for row in cursor:
                            totchem.append(row)
                    totchem.sort()
                    tupmax = totchem[-1]
                    chemmax = tupmax[0]

                    # Expand chemical agents fields
                    fieldnum = 1
                    while fieldnum <= chemmax:
                        selfc = "PropTRADE_NM" + str(fieldnum)
                        ChemSel = str("chem_ct = " + str(fieldnum))
                        fieldname = "TRADE_NM" + str(fieldnum)
                        fieldlist = ["MNFCTR_NM", "SITE_TX", "APP_RT_TX", "APP_AMT_LOW", "APP_AMT_HIGH", "ROLE_NM", "CERT_NR"]
                        arcpy.analysis.TableSelect("PropChemSort", selfc, ChemSel)
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=40)
                            arcpy.management.CalculateField(selfc, fieldname, "!TRADE_NM!", "PYTHON3")
                            for item in fieldlist:
                                for field in arcpy.ListFields(selfc, item):
                                    fldnm = str(field.name)
                                    fieldname2 = fldnm + str(fieldnum)
                                    if "OID" in field.type:
                                        arcpy.AddMessage("This is an ESRI Field Type")
                                    elif "String" in field.type:
                                        arcpy.management.AddField(selfc, fieldname2, "TEXT", field_length=field.length)
                                    else:
                                        arcpy.AddMessage(str(field.type))
                                        arcpy.management.AddField(selfc, fieldname2, field.type)
                                        arcpy.management.CalculateField(selfc, fieldname2, "!" + fldnm + "!", "PYTHON3")
                            (fieldname3, fieldname4, fieldname5, fieldname6, fieldname7, fieldname8, fieldname9, fieldname10) = "TRADE_NM" + str(fieldnum), "MNFCTR_NM" + str(fieldnum), "SITE_TX" + str(fieldnum), "APP_RT_TX" + str(fieldnum), "APP_AMT_LOW" + str(fieldnum), "APP_AMT_HIGH" + str(fieldnum), "ROLE_NM" + str(fieldnum), "CERT_NR" + str(fieldnum)
                            arcpy.management.JoinField("PropTRADE_NM1", "PROP_TRT_GUID", selfc, "PROP_TRT_GUID", [fieldname3, fieldname4, fieldname5, fieldname6, fieldname7, fieldname8, fieldname9, fieldname10])
                        fieldnum += 1
                    arcpy.management.DeleteField("PropTRADE_NM1", ["guid_txt", "chem_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "PropTRADE_NM1", InGDB + "\\PROPOSALCHEMCOMPCONTROLAGENT")

                # Join CHEMICAL data with PROPOSAL data
                arcpy.management.JoinField("ProposedLoc_Select", "PROP_TRT_GUID", "PropTRADE_NM1", "PROP_TRT_GUID")
                arcpy.management.DeleteField("ProposedLoc_Select", ["CLCACRE_ME_1", "SUM_EST_CVR_RT_1", "RCMDCCA_ME", "CCA_UOM_NM", "TRT_CMP_ID", "PROP_TRT_GUID_1", "TRT_PRP_ID_1", "LE_ID", "FEATURE_ID", "TRT_PRP_ID", "RIPS_NR", "BCP_NR", "BPS_NR", "ORG_CD", "FLD_OFF_LE", "FO_APPCD", "FO_APPDT", "ST_COORD_LE", "COOR_APPCD", "COOR_APPDT", "ST_DIR_LE", "DIR_APPCD", "DIR_APPDT", "FO_CM_TX", "CO_CM_TX", "DIR_CM_TX"])
                arcpy.analysis.Select("ProposedLoc_Select", finalgdb + "\\ProposedBiologicalData", "BIO_SCNTFC_CD IS NOT NULL")
                pbio_data = finalgdb + "\\ProposedBiologicalData"
                pbio_source = Metadata + "\\ProposedBiologicalData_export.xml"
                pbio_md = md.Metadata(pbio_data)
                if not pbio_md.isReadOnly:
                    pbio_md.importMetadata(pbio_source, 'FGDC_CSDGM')
                    pbio_md.save()
                bioct = arcpy.management.GetCount(finalgdb + "\\ProposedBiologicalData").getOutput(0)
                if int(bioct) == 0:
                    arcpy.management.Delete(finalgdb + "\\ProposedBiologicalData")
                arcpy.analysis.Select("ProposedLoc_Select", finalgdb + "\\ProposedChemicalData", "TRADE_NM IS NOT NULL")
                pchem_data = finalgdb + "\\ProposedChemicalData"
                pchem_source = Metadata + "\\ProposedChemicalData_export.xml"
                pchem_md = md.Metadata(pchem_data)
                if not pchem_md.isReadOnly:
                    pchem_md.importMetadata(pchem_source, 'FGDC_CSDGM')
                    pchem_md.save()
                chemct = arcpy.management.GetCount(finalgdb + "\\ProposedChemicalData").getOutput(0)
                if int(chemct) == 0:
                    arcpy.management.Delete(finalgdb + "\\ProposedChemicalData")
                arcpy.analysis.Select("ProposedLoc_Select", finalgdb + "\\ProposedOtherData", "BIO_SCNTFC_CD IS NULL AND TRADE_NM IS NULL")
                poth_data = finalgdb + "\\ProposedOtherData"
                poth_source = Metadata + "\\ProposedOtherData_export.xml"
                poth_md = md.Metadata(poth_data)
                if not poth_md.isReadOnly:
                    poth_md.importMetadata(poth_source, 'FGDC_CSDGM')
                    poth_md.save()
                othct = arcpy.management.GetCount(finalgdb + "\\ProposedOtherData").getOutput(0)
                if int(othct) == 0:
                    arcpy.management.Delete(finalgdb + "\\ProposedOtherData")

    # Select TREATMENT data
    arcpy.AddMessage("Treatment data being compiled.")
    if "All Treatment" in DataType or "Biological" in DataType or "Chemical" in DataType or "Fire" in DataType or "Manual" in DataType or "Mechanical" in DataType or "Revegetation" in DataType:
        fcct = arcpy.management.GetCount(InGDB + "\\TreatmentComponentLocation").getOutput(0)
        if int(fcct) > 0:
            arcpy.analysis.Select(InGDB + "\\TreatmentComponentLocation", "TreatmentLoc_Select", TrtSel)
            arcpy.management.DeleteField("TreatmentLoc_Select", "TRT_QTY")
            trtct = arcpy.management.GetCount("TreatmentLoc_Select").getOutput(0)
            if int(trtct) > 0:

                # Number the Species for each GUID
                arcpy.management.CopyRows(InGDB + "\\TREATMENTSPECIES", "in_memory\\TrtSpp")
                arcpy.management.JoinField("in_memory\\TrtSpp", "TRT_GUID", "TreatmentLoc_Select", "TRT_GUID", "TRT_GUID")
                arcpy.analysis.TableSelect("in_memory\\TrtSpp", "TrtSppSel", "TRT_GUID = TRT_GUID_1")
                arcpy.management.DeleteField("TrtSppSel", "TRT_GUID_1")
                arcpy.management.MakeQueryTable("TrtSppSel", "TrtSppSel2", "ADD_VIRTUAL_KEY_FIELD", "", ["TRT_GUID", "SCNTFC_CD", "EST_CVR_RT", "TRT_QTY"])
                arcpy.management.CopyRows("TrtSppSel2", "TrtSppSel3")
                arcpy.management.AddField("TrtSppSel3", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("TrtSppSel3", "guid_txt", "!TRT_GUID!", "PYTHON3")
                arcpy.management.Sort("TrtSppSel3", "TrtSppSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("TrtSppSort", "spp_ct", "SHORT")
                arcpy.management.CalculateField("TrtSppSort", "spp_ct", "GetDupCt(!TRT_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of species
                sppct = arcpy.management.GetCount("TrtSppSort").getOutput(0)
                if int(sppct) > 0:
                    totspp = []
                    with arcpy.da.SearchCursor("TrtSppSort", ["spp_ct"]) as cursor:
                        for row in cursor:
                            totspp.append(row)
                    totspp.sort()
                    tupmax = totspp[-1]
                    sppmax = tupmax[0]

                    # Expand species fields
                    fieldnum = 1
                    while fieldnum <= sppmax:
                        selfc = "TrtSCNTFC_CD" + str(fieldnum)
                        SppSel = str("spp_ct = " + str(fieldnum))
                        fieldname = "SCNTFC_CD" + str(fieldnum)
                        fieldname2 = "EST_CVR_RT" + str(fieldnum)
                        fieldname3 = "TRT_QTY" + str(fieldnum)
                        arcpy.analysis.TableSelect("TrtSppSort", selfc, SppSel)
                        arcpy.management.AssignDomainToField(selfc, "SCNTFC_CD", "domSCNTFC_CD")
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=10)
                            arcpy.management.CalculateField(selfc, fieldname, "!SCNTFC_CD!", "PYTHON3")
                            arcpy.management.AssignDomainToField(selfc, fieldname, "domSCNTFC_CD")
                            arcpy.management.AddField(selfc, fieldname2, "DOUBLE")
                            arcpy.management.CalculateField(selfc, fieldname2, "!EST_CVR_RT!", "PYTHON3")
                            arcpy.management.AddField(selfc, fieldname3, "LONG")
                            arcpy.management.CalculateField(selfc, fieldname3, "!TRT_QTY!", "PYTHON3")
                            arcpy.management.JoinField("TrtSCNTFC_CD1", "TRT_GUID", selfc, "TRT_GUID", [fieldname, fieldname2, fieldname3])
                        fieldnum += 1
                    arcpy.management.DeleteField("TrtSCNTFC_CD1", ["guid_txt", "spp_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "TrtSCNTFC_CD1", InGDB + "\\TREATMENTSPECIES")

                # Join SPECIES data with TREATMENT data
                arcpy.management.JoinField("TreatmentLoc_Select", "TRT_GUID", "TrtSCNTFC_CD1", "TRT_GUID")
                arcpy.management.DeleteField("TreatmentLoc_Select", ["TRT_GUID_1", "TRT_QTY_1", "TRT_CMP_ID", "FEATURE_ID", "OTHACRE_ME", "BLMACRE_ME", "PRVACRE_ME", "BLM_FO_CD", "LE_ID", "TRT_PRP_ID", "INTRVL_NM", "FR_DSTB_FL", "REQ_NR", "FINANCE_CD", "ASSTAGR_NM", "SALIN_FLAG", "ESR_NR", "ESR_TRT_FL", "RIPS_NR", "MGMT_CAT", "COOP_FLAG", "FIRE_NR", "FORVIS_ID", "TRT_GOAL", "CAUSE_CAT", "CAUSE_DTL", "CMRCL_FLAG", "SALVG_FLAG", "CNTRCT_CD", "TRT_UNITNO", "TRT_STATUS", "INITIAL_CD", "EVENTID"])
                arcpy.management.CopyFeatures("TreatmentLoc_Select", workcopy + "\\TreatmentLoc_withspp")

                # Select BIOLOGICAL data
                arcpy.AddMessage("Biological treatment data being compiled.")
                if "All Treatment" in DataType or "Biological" in DataType:
                    arcpy.analysis.Select("TreatmentLoc_Select", "BiologicalLoc_Select", "CMP_TY_NM = \'BIOLOGICAL\'")
                    bioct = arcpy.management.GetCount("BiologicalLoc_Select").getOutput(0)
                    if int(bioct) > 0:

                        # Join BIOLOGICAL data with TREATMENT data
                        arcpy.management.JoinField("BiologicalLoc_Select", "TRT_GUID", InGDB + "\\BIOLOGICALCOMPONENT", "TRT_GUID")
                        arcpy.management.DeleteField("BiologicalLoc_Select", ["TRT_GUID_1", "TRT_CMP_ID", "SPECIES_ID", "SRCE_LE_ID", "AUT_LE_ID", "ORG_ID"])
                        arcpy.management.CopyFeatures("BiologicalLoc_Select", finalgdb + "\\BiologicalTreatmentData")
                        bio_data = finalgdb + "\\BiologicalTreatmentData"
                        bio_source = Metadata + "\\BiologicalTreatmentData_export.xml"
                        bio_md = md.Metadata(bio_data)
                        if not bio_md.isReadOnly:
                            bio_md.importMetadata(bio_source, 'FGDC_CSDGM')
                            bio_md.save()

                # Select CHEMICAL data
                arcpy.AddMessage("Chemical treatment data being compiled.")
                if "All Treatment" in DataType or "Chemical" in DataType:
                    arcpy.analysis.Select("TreatmentLoc_Select", "ChemicalLoc_Select", "CMP_TY_NM = \'CHEMICAL\'")
                    chemct = arcpy.management.GetCount("ChemicalLoc_Select").getOutput(0)
                    if int(chemct) > 0:

                        # Join CHEMICAL data with TREATMENT data
                        arcpy.management.JoinField("ChemicalLoc_Select", "TRT_GUID", InGDB + "\\CHEMICALCOMPONENT", "TRT_GUID")
                        arcpy.management.DeleteField("ChemicalLoc_Select", ["TRT_GUID_1", "TRT_CMP_ID", "CH_PRPS_NM", "ESTACRC_CD", "EQ_CAP_TX", "EQ_PRPS_TX", "EQ_PRTY_NM"])

                        # Number the Chemical Agents for each GUID
                        arcpy.management.CopyRows(InGDB + "\\CHEMICALCOMPCONTROLAGENT", "in_memory\\TrtChem")
                        arcpy.management.JoinField("in_memory\\TrtChem", "TRT_GUID", "ChemicalLoc_Select", "TRT_GUID", "TRT_GUID")
                        arcpy.analysis.TableSelect("in_memory\\TrtChem", "TrtChemSel", "TRT_GUID = TRT_GUID_1")
                        arcpy.management.DeleteField("TrtChemSel", "TRT_GUID_1")
                        arcpy.management.AddField("TrtChemSel", "guid_txt", "TEXT", field_length=50)
                        arcpy.management.CalculateField("TrtChemSel", "guid_txt", "!TRT_GUID!", "PYTHON3")
                        arcpy.management.Sort("TrtChemSel", "TrtChemSort", [["guid_txt", "ASCENDING"]])
                        arcpy.management.AddField("TrtChemSort", "chem_ct", "SHORT")
                        arcpy.management.CalculateField("TrtChemSort", "chem_ct", "GetDupCt(!TRT_GUID!)", "PYTHON3", dupct_cb)

                        # Get the maximum number of chemical agents
                        chemct = arcpy.management.GetCount("TrtChemSort").getOutput(0)
                        if int(chemct) > 0:
                            totchem = []
                            with arcpy.da.SearchCursor("TrtChemSort", ["chem_ct"]) as cursor:
                                for row in cursor:
                                    totchem.append(row)
                            totchem.sort()
                            tupmax = totchem[-1]
                            chemmax = tupmax[0]

                            # Expand chemical agents fields
                            fieldnum = 1
                            while fieldnum <= chemmax:
                                selfc = "TrtTRADE_NM" + str(fieldnum)
                                ChemSel = str("chem_ct = " + str(fieldnum))
                                fieldname = "TRADE_NM" + str(fieldnum)
                                fieldlist = ["ACTLUSE_QY", "AGT_UOM_NM", "AGT_APP_RT", "APP_UOM_NM", "MNFCTR_NM", "EPAREGISTRATIONNUMBER", "CONAGT_GUID"]
                                arcpy.analysis.TableSelect("TrtChemSort", selfc, ChemSel)
                                if fieldnum > 1:
                                    arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=40)
                                    arcpy.management.CalculateField(selfc, fieldname, "!TRADE_NM!", "PYTHON3")
                                    for item in fieldlist:
                                        for field in arcpy.ListFields(selfc, str(item)):
                                            fldnm = str(field.name)
                                            fieldname2 = fldnm + str(fieldnum)
                                            if "String" in field.type:
                                                arcpy.management.AddField(selfc, fieldname2, "TEXT", field_length=field.length)
                                            else:
                                                arcpy.management.AddField(selfc, fieldname2, field.type)
                                            arcpy.management.CalculateField(selfc, fieldname2, "!" + fldnm + "!", "PYTHON3")
                                    (fieldname3, fieldname4, fieldname5, fieldname6, fieldname7, fieldname8, fieldname9, fieldname10) = "TRADE_NM" + str(fieldnum), "ACTLUSE_QY" + str(fieldnum), "AGT_UOM_NM" + str(fieldnum), "AGT_APP_RT" + str(fieldnum), "APP_UOM_NM" + str(fieldnum), "MNFCTR_NM" + str(fieldnum), "EPAREGISTRATIONNUMBER" + str(fieldnum), "CONAGT_GUID" + str(fieldnum)
                                    arcpy.management.JoinField("TrtTRADE_NM1", "TRT_GUID", selfc, "TRT_GUID", [fieldname3, fieldname4, fieldname5, fieldname6, fieldname7, fieldname8, fieldname9, fieldname10])
                                fieldnum += 1
                            arcpy.management.DeleteField("TrtTRADE_NM1", ["guid_txt", "chem_ct"])
                        else:
                            arcpy.management.CreateTable(workcopy, "TrtTRADE_NM1", InGDB + "\\CHEMICALCOMPCONTROLAGENT")

                        # Join CHEMICAL AGENT data with CHEMICAL data
                        arcpy.management.JoinField("ChemicalLoc_Select", "TRT_GUID", "TrtTRADE_NM1", "TRT_GUID")
                        arcpy.management.DeleteField("ChemicalLoc_Select", "TRT_GUID_1")

                        # Number the Adjuvants for each GUID
                        arcpy.management.CopyRows(InGDB + "\\ADJUVANTCOMPONENTAGENT", "in_memory\\TrtAdj")
                        adjct = arcpy.management.GetCount("in_memory\\TrtAdj").getOutput(0)
                        if int(adjct) > 0:
                            arcpy.management.JoinField("in_memory\\TrtAdj", "TRT_GUID", "ChemicalLoc_Select", "TRT_GUID", "TRT_GUID")
                            arcpy.analysis.TableSelect("in_memory\\TrtAdj", "TrtAdjSel", "TRT_GUID = TRT_GUID_1")
                            arcpy.management.DeleteField("TrtAdjSel", "TRT_GUID_1")
                            arcpy.management.AddField("TrtAdjSel", "guid_txt", "TEXT", field_length=50)
                            arcpy.management.CalculateField("TrtAdjSel", "guid_txt", "!TRT_GUID!", "PYTHON3")
                            arcpy.management.Sort("TrtAdjSel", "TrtAdjSort", [["guid_txt", "ASCENDING"]])
                            arcpy.management.AddField("TrtAdjSort", "adj_ct", "SHORT")
                            arcpy.management.CalculateField("TrtAdjSort", "adj_ct", "GetDupCt(!TRT_GUID!)", "PYTHON3", dupct_cb)

                            # Get the maximum number of adjuvants
                            adjct = arcpy.management.GetCount("TrtAdjSort").getOutput(0)
                            if int(adjct) > 0:
                                totadj = []
                                with arcpy.da.SearchCursor("TrtAdjSort", ["adj_ct"]) as cursor:
                                    for row in cursor:
                                        totadj.append(row)
                                totadj.sort()
                                tupmax = totadj[-1]
                                adjmax = tupmax[0]

                                # Expand adjuvants fields
                                fieldnum = 1
                                while fieldnum <= adjmax:
                                    selfc = "TrtADJTRADE_NM" + str(fieldnum)
                                    AdjSel = str("adj_ct = " + str(fieldnum))
                                    if fieldnum == 1:
                                        fieldname = "ADJ_TRADE_NM"
                                    else:
                                        fieldname = "ADJ_TRADE_NM" + str(fieldnum)
                                    fieldlist = ["ACTLUSE_QTY", "APP_UOM_NM", "AGT_APP_RT", "AGT_UOM_NM"]
                                    arcpy.analysis.TableSelect("TrtAdjSort", selfc, AdjSel)
                                    arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=40)
                                    arcpy.management.CalculateField(selfc, fieldname, "!TRADE_NM!", "PYTHON3")
                                    for item in fieldlist:
                                        for field in arcpy.ListFields(selfc, str(item)):
                                            fldnm = str(field.name)
                                            if fieldnum == 1:
                                                fieldname2 = "ADJ_" + fldnm
                                            else:
                                                fieldname2 = "ADJ_" + fldnm + str(fieldnum)
                                            if "String" in field.type:
                                                arcpy.management.AddField(selfc, fieldname2, "TEXT", field_length=field.length)
                                            else:
                                                arcpy.management.AddField(selfc, fieldname2, field.type)
                                            arcpy.management.CalculateField(selfc, fieldname2, "!" + fldnm + "!", "PYTHON3")
                                    # FIX: JoinField call was inside the 'for item' loop, causing it to run
                                    # multiple times per fieldnum iteration; moved to correct scope
                                    if fieldnum > 1:
                                        (fieldname3, fieldname4, fieldname5, fieldname6, fieldname7) = "ADJ_TRADE_NM" + str(fieldnum), "ADJ_ACTLUSE_QTY" + str(fieldnum), "ADJ_AGT_UOM_NM" + str(fieldnum), "ADJ_AGT_APP_RT" + str(fieldnum), "ADJ_APP_UOM_NM" + str(fieldnum)
                                        arcpy.management.JoinField("TrtADJTRADE_NM1", "TRT_GUID", selfc, "TRT_GUID", [fieldname3, fieldname4, fieldname5, fieldname6, fieldname7])
                                    fieldnum += 1
                                arcpy.management.DeleteField("TrtADJTRADE_NM1", ["guid_txt", "adj_ct", "TRADE_NM", "ACTLUSE_QTY", "AGT_UOM_NM", "AGT_APP_RT", "APP_UOM_NM"])
                                for field in arcpy.ListFields("TrtADJTRADE_NM1", "*_1*"):
                                    arcpy.management.DeleteField("TrtADJTRADE_NM1", field.name)
                            else:
                                arcpy.management.CreateTable(workcopy, "TrtADJTRADE_NM1")
                                arcpy.management.AddField("TrtADJTRADE_NM1", "ADJ_TRADE_NM", "TEXT", field_length=40)
                                arcpy.management.AddField("TrtADJTRADE_NM1", "ADJ_ACTLUSE_QTY", "DOUBLE")
                                arcpy.management.AddField("TrtADJTRADE_NM1", "ADJ_AGT_UOM_NM", "TEXT", field_length=30)
                                arcpy.management.AddField("TrtADJTRADE_NM1", "ADJ_AGT_APP_RT", "DOUBLE")
                                arcpy.management.AddField("TrtADJTRADE_NM1", "ADJ_APP_UOM_NM", "TEXT", field_length=30)
                                arcpy.management.AddField("TrtADJTRADE_NM1", "TRT_GUID", "GUID")

                            # Join ADJUVANT data with CHEMICAL data
                            arcpy.management.JoinField("ChemicalLoc_Select", "TRT_GUID", "TrtADJTRADE_NM1", "TRT_GUID")
                            arcpy.management.DeleteField("ChemicalLoc_Select", ["TRT_GUID_1", "TRT_CMP_ID_1"])
                        arcpy.management.CopyFeatures("ChemicalLoc_Select", finalgdb + "\\ChemicalTreatmentData")
                        chem_data = finalgdb + "\\ChemicalTreatmentData"
                        chem_source = Metadata + "\\ChemicalTreatmentData_export.xml"
                        chem_md = md.Metadata(chem_data)
                        if not chem_md.isReadOnly:
                            chem_md.importMetadata(chem_source, 'FGDC_CSDGM')
                            chem_md.save()

                # Select FIRE data
                arcpy.AddMessage("Fire treatment data being compiled.")
                if "All Treatment" in DataType or "Fire" in DataType:
                    arcpy.analysis.Select("TreatmentLoc_Select", "FireLoc_Select", "CMP_TY_NM = \'FIRE\'")
                    firect = arcpy.management.GetCount("FireLoc_Select").getOutput(0)
                    if int(firect) > 0:

                        # Join FIRE data with TREATMENT data
                        arcpy.management.JoinField("FireLoc_Select", "TRT_GUID", InGDB + "\\FIRECOMPONENT", "TRT_GUID")
                        arcpy.management.DeleteField("FireLoc_Select", ["TRT_GUID_1", "TRT_CMP_ID", "MOSAIC_TX", "BEFBURN_TX", "FRSTART_NM", "AFTBURN_TX"])
                        arcpy.management.CopyFeatures("FireLoc_Select", finalgdb + "\\FireTreatmentData")
                        fire_data = finalgdb + "\\FireTreatmentData"
                        fire_source = Metadata + "\\FireTreatmentData_export.xml"
                        fire_md = md.Metadata(fire_data)
                        if not fire_md.isReadOnly:
                            fire_md.importMetadata(fire_source, 'FGDC_CSDGM')
                            fire_md.save()

                # Select MANUAL data
                arcpy.AddMessage("Manual treatment data being compiled.")
                if "All Treatment" in DataType or "Manual" in DataType:
                    arcpy.analysis.Select("TreatmentLoc_Select", "ManualLoc_Select", "CMP_TY_NM = \'MANUAL\'")
                    manct = arcpy.management.GetCount("ManualLoc_Select").getOutput(0)
                    if int(manct) > 0:

                        # Join MANUAL data with TREATMENT data
                        arcpy.management.JoinField("ManualLoc_Select", "TRT_GUID", InGDB + "\\MANUALCOMPONENT", "TRT_GUID")
                        arcpy.management.DeleteField("ManualLoc_Select", ["TRT_GUID_1", "TRT_CMP_ID", "HT_TYPE"])
                        arcpy.management.CopyFeatures("ManualLoc_Select", finalgdb + "\\ManualTreatmentData")
                        man_data = finalgdb + "\\ManualTreatmentData"
                        man_source = Metadata + "\\ManualTreatmentData_export.xml"
                        man_md = md.Metadata(man_data)
                        if not man_md.isReadOnly:
                            man_md.importMetadata(man_source, 'FGDC_CSDGM')
                            man_md.save()

                # Select MECHANICAL data
                arcpy.AddMessage("Mechanical treatment data being compiled.")
                if "All Treatment" in DataType or "Mechanical" in DataType:
                    arcpy.analysis.Select("TreatmentLoc_Select", "MechanicalLoc_Select", "CMP_TY_NM = \'MECHANICAL\'")
                    mechct = arcpy.management.GetCount("MechanicalLoc_Select").getOutput(0)
                    if int(mechct) > 0:

                        # Join MECHANICAL data with TREATMENT data
                        arcpy.management.JoinField("MechanicalLoc_Select", "TRT_GUID", InGDB + "\\MECHANICALCOMPONENT", "TRT_GUID")
                        arcpy.management.DeleteField("MechanicalLoc_Select", ["TRT_GUID_1", "TRT_CMP_ID", "HT_TYPE"])
                        arcpy.management.CopyFeatures("MechanicalLoc_Select", finalgdb + "\\MechanicalTreatmentData")
                        mech_data = finalgdb + "\\MechanicalTreatmentData"
                        mech_source = Metadata + "\\MechanicalTreatmentData_export.xml"
                        mech_md = md.Metadata(mech_data)
                        if not mech_md.isReadOnly:
                            mech_md.importMetadata(mech_source, 'FGDC_CSDGM')
                            mech_md.save()

                # Select REVEGETATION data
                arcpy.AddMessage("Revegetation treatment data being compiled.")
                if "All Treatment" in DataType or "Revegetation" in DataType:
                    arcpy.analysis.Select("TreatmentLoc_Select", "RevegetationLoc_Select", "CMP_TY_NM = \'REVEGETATION\'")
                    revct = arcpy.management.GetCount("RevegetationLoc_Select").getOutput(0)
                    if int(revct) > 0:

                        # Join REVEGETATION data with TREATMENT data
                        arcpy.management.AddField("RevegetationLoc_Select", "RVG_PHNLGY_NM", "TEXT", field_length=20)
                        arcpy.management.CalculateField("RevegetationLoc_Select", "RVG_PHNLGY_NM", "!PHNLGY_NM!", "PYTHON3")
                        arcpy.management.DeleteField("RevegetationLoc_Select", "PHNLGY_NM")
                        arcpy.management.JoinField("RevegetationLoc_Select", "TRT_GUID", InGDB + "\\REVEGETATIONCOMPONENT", "TRT_GUID")
                        arcpy.management.DeleteField("RevegetationLoc_Select", ["TRT_GUID_1", "TRT_CMP_ID", "SPECIES_ID", "STOCK_ME_1", "VEG_UOM_NM_1"])
                        arcpy.management.CopyFeatures("RevegetationLoc_Select", finalgdb + "\\RevegetationTreatmentData")
                        rev_data = finalgdb + "\\RevegetationTreatmentData"
                        rev_source = Metadata + "\\RevegetationTreatmentData_export.xml"
                        rev_md = md.Metadata(rev_data)
                        if not rev_md.isReadOnly:
                            rev_md.importMetadata(rev_source, 'FGDC_CSDGM')
                            rev_md.save()
                            
                # Select RESTORATION data
                arcpy.AddMessage("Restoration treatment data being compiled.")
                if "All Treatment" in DataType or "Restoration" in DataType:
                    arcpy.analysis.Select("TreatmentLoc_Select", "RestorationLoc_Select", "CMP_TY_NM = \'RESTORATION\'")
                    restct = arcpy.management.GetCount("RestorationLoc_Select").getOutput(0)
                    if int(restct) > 0:

                        # Join RESTORATION data with TREATMENT data
                        arcpy.management.JoinField("RestorationLoc_Select", "TRT_GUID", InGDB + "\\RESTORATIONCOMPONENT", "TRT_GUID")
                        arcpy.management.DeleteField("RestorationLoc_Select", ["TRT_GUID_1", "TRT_CMP_ID"])
                        arcpy.management.CopyFeatures("RestorationLoc_Select", finalgdb + "\\RestorationTreatmentData")
                        rest_data = finalgdb + "\\RestorationTreatmentData"
                        rest_source = Metadata + "\\RestorationTreatmentData_export.xml"
                        rest_md = md.Metadata(rest_data)
                        if not rest_md.isReadOnly:
                            rest_md.importMetadata(rest_source, 'FGDC_CSDGM')
                            rest_md.save()

    # Select PHOTO data
    arcpy.AddMessage("Photo data being compiled")
    if "Photo" in DataType:
        fcct = arcpy.management.GetCount(InGDB + "\\PhotoLocation").getOutput(0)
        if int(fcct) > 0:
            arcpy.analysis.Select(InGDB + "\\PhotoLocation", "PhotoLoc_Select", PhotSel)
            plocct = arcpy.management.GetCount("PhotoLoc_Select").getOutput(0)
            if int(plocct) > 0:

                # Number the photos for each GUID
                arcpy.management.CopyRows(InGDB + "\\PHOTOS", "in_memory\\Photos")
                arcpy.management.JoinField("in_memory\\Photos", "PHOTO_GUID", "PhotoLoc_Select", "PHOTO_GUID", "PHOTO_GUID")
                arcpy.analysis.TableSelect("in_memory\\Photos", "PhotosSel", "PHOTO_GUID = PHOTO_GUID_1")
                arcpy.management.DeleteField("PhotosSel", "PHOTO_GUID_1")
                arcpy.management.AddField("PhotosSel", "guid_txt", "TEXT", field_length=50)
                arcpy.management.CalculateField("PhotosSel", "guid_txt", "!PHOTO_GUID!", "PYTHON3")
                arcpy.management.Sort("PhotosSel", "PhotosSort", [["guid_txt", "ASCENDING"]])
                arcpy.management.AddField("PhotosSort", "phot_ct", "SHORT")
                arcpy.management.CalculateField("PhotosSort", "phot_ct", "GetDupCt(!PHOTO_GUID!)", "PYTHON3", dupct_cb)

                # Get the maximum number of photos
                photct = arcpy.management.GetCount("PhotosSort").getOutput(0)
                if int(photct) > 0:
                    totphot = []
                    with arcpy.da.SearchCursor("PhotosSort", ["phot_ct"]) as cursor:
                        for row in cursor:
                            totphot.append(row)
                    totphot.sort()
                    tupmax = totphot[-1]
                    photmax = tupmax[0]

                    # Expand PHOTO fields
                    fieldnum = 1
                    while fieldnum <= photmax:
                        selfc = "PhtPHOTO" + str(fieldnum)
                        PhotSel2 = str("phot_ct = " + str(fieldnum))
                        fieldname = "PHOTO" + str(fieldnum)
                        fieldlist = ["PHOTODIREC", "PREFIX", "PHOTONUM", "PURPOSE", "PHOTODATE", "PHOTODEG"]
                        arcpy.analysis.TableSelect("PhotosSort", selfc, PhotSel2)
                        if fieldnum > 1:
                            arcpy.management.AddField(selfc, fieldname, "TEXT", field_length=200)
                            arcpy.management.CalculateField(selfc, fieldname, "!PHOTO!", "PYTHON3")
                            for item in fieldlist:
                                for field in arcpy.ListFields(selfc, str(item)):
                                    fldnm = str(field.name)
                                    fieldname2 = fldnm + str(fieldnum)
                                    if "String" in field.type:
                                        arcpy.management.AddField(selfc, fieldname2, "TEXT", field_length=field.length)
                                    else:
                                        arcpy.management.AddField(selfc, fieldname2, field.type)
                                    arcpy.management.CalculateField(selfc, fieldname2, "!" + fldnm + "!", "PYTHON3")
                            (fieldname3, fieldname4, fieldname5, fieldname6, fieldname7, fieldname8, fieldname9) = "PHOTO" + str(fieldnum), "PHOTODIREC" + str(fieldnum), "PREFIX" + str(fieldnum), "PHOTONUM" + str(fieldnum), "PURPOSE" + str(fieldnum), "PHOTODATE" + str(fieldnum), "PHOTODEG" + str(fieldnum)
                            arcpy.management.JoinField("PhtPHOTO1", "PHOTO_GUID", selfc, "PHOTO_GUID", [fieldname3, fieldname4, fieldname5, fieldname6, fieldname7, fieldname8, fieldname9])
                        fieldnum += 1
                    arcpy.management.DeleteField("PhtPHOTO1", ["guid_txt", "phot_ct"])
                else:
                    arcpy.management.CreateTable(workcopy, "PhtPHOTO1", InGDB + "\\PHOTOS")

                # Join PHOTO data with PhotoLocation data
                arcpy.management.JoinField("PhotoLoc_Select", "PHOTO_GUID", "PhtPHOTO1", "PHOTO_GUID")
                arcpy.analysis.Select("PhotoLoc_Select", "PhotoLoc_Date", PhDtSel)
                arcpy.management.DeleteField("PhotoLoc_Date", ["PHOTO_GUID_1", "FEATURE_ID_1", "FEATURE_ID", "EventID"])
                arcpy.management.CopyFeatures("PhotoLoc_Date", finalgdb + "\\PhotoLocation")
                photo_data = finalgdb + "\\PhotoLocation"
                photo_source = Metadata + "\\PhotoLocation_export.xml"
                photo_md = md.Metadata(photo_data)
                if not photo_md.isReadOnly:
                    photo_md.importMetadata(photo_source, 'FGDC_CSDGM')
                    photo_md.save()


except:

    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n      " + str(sys.exc_info()[1])
    msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    arcpy.AddError(msgs)
    arcpy.AddError(pymsg)

arcpy.management.Delete("in_memory")
