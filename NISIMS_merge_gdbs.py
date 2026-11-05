#----------------------------------------------------------------------------------------------------------------------
# Name: NISIMS_merge_gdbs.py
# Purpose: This script was created to automate the merging of feature classes within multiple NISIMS uploads.
# Author: Jennifer Sieracki
# Created: 2025-03-12 11:21am
#----------------------------------------------------------------------------------------------------------------------

# Import modules
import arcpy
import sys
import traceback
import time


def merge_fc(fctype):
    """Purpose: Merge matching feature classes
    Parameters:
        fctype: The feature class type that will be merged
    …
    Return: None
    """
    
    fcwld = str(fctype + "_*")
    fclist = arcpy.ListFeatureClasses(fcwld)
    listct = len(fclist)
    if listct > 0:
        arcpy.AddMessage("Merging " + fctype)
        arcpy.management.Merge(fclist, fctype)
        for fc in arcpy.ListFeatureClasses(fcwld):
            arcpy.management.Delete(fc)
    else:
        arcpy.AddMessage("No feature classes merged.")

        
def main():
    try:
        arcpy.env.workspace = UpGDB

        fcct = 1
        for gdb in arcpy.ListWorkspaces():
            arcpy.env.workspace = gdb
            arcpy.AddMessage("GDB: " + gdb)
            
            for fc in arcpy.ListFeatureClasses():
                arcpy.AddMessage("Processing " + fc)
                arcpy.management.CopyFeatures(fc, Mergegdb +"\\" + fc + "_" + str(fcct))
                fcct += 1

        arcpy.env.workspace = Mergegdb
        merge_fc("BiologicalTreatmentData")
        merge_fc("ChemicalTreatmentData")
        merge_fc("FireTreatmentData")
        merge_fc("ManualTreatmentData")
        merge_fc("MechanicalTreatmentData")
        merge_fc("RestorationTreatmentData")
        merge_fc("RevegetationTreatmentData")
        merge_fc("ProposedBiologicalData")
        merge_fc("ProposedChemicalData")
        merge_fc("ProposedOtherData")
        merge_fc("WeedInfestationData")
        merge_fc("WeedSurveyData")
        
        
    except Exception as e:

        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n      " + str(sys.exc_info()[1])
        msgs = "ARCPY ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(e)
        arcpy.AddError(msgs)
        arcpy.AddError(pymsg)

    finally:
        arcpy.Delete_management("memory")


if __name__ == '__main__':
    
    # Input variables
    UpGDB = arcpy.GetParameterAsText(0)
    Mergegdb = arcpy.GetParameterAsText(1)

    main()
