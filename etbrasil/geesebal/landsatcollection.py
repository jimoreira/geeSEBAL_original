#----------------------------------------------------------------------------------------#
#---------------------------------------//GEESEBAL//-------------------------------------#
#GEESEBAL - GOOGLE EARTH ENGINE APP FOR SURFACE ENERGY BALANCE ALGORITHM FOR LAND (SEBAL)
#CREATE BY: LEONARDO LAIPELT, RAFAEL KAYSER, ANDERSON RUHOFF AND AYAN FLEISCHMANN
#PROJECT - ET BRASIL https://etbrasil.org/
#LAB - HIDROLOGIA DE GRANDE ESCALA [HGE] website: https://www.ufrgs.br/hge/author/hge/
#UNIVERSITY - UNIVERSIDADE FEDERAL DO RIO GRANDE DO SUL - UFRGS
#RIO GRANDE DO SUL, BRAZIL

#DOI
#VERSION 0.1.1
#CONTACT US: leonardo.laipelt@ufrgs.br

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------#

#PYTHON PACKAGES
#Call EE
import ee

#SURFACE REFLECTANCE
#ATMOSPHERICALLY CORRECTED

#get landsat 9
def fexp_landsat_9PathRow(start_date,end_date,n_path, n_row,th_cloud_cover):
    col_SR_L9 =(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
                        .filterDate(start_date, end_date)
                        .filterMetadata('WRS_PATH', 'equals', n_path)
                        .filterMetadata('WRS_ROW', 'equals', n_row)
                        .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6' ,'SR_B7' ,'ST_B10','QA_PIXEL'],
                               ["UB"   ,"B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","SWIR_2","BRT"   ,"pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));
    return col_SR_L9;
#
#GET LANDSAT 8 COLLECTIONS BY PATH ROW
def fexp_landsat_8PathRow(start_date,end_date,n_path, n_row,th_cloud_cover):
    col_SR_L8 =(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                        .filterDate(start_date, end_date)
                        .filterMetadata('WRS_PATH', 'equals', n_path)
                        .filterMetadata('WRS_ROW', 'equals', n_row)
                        .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6' ,'SR_B7' ,'ST_B10','QA_PIXEL'],
                               ["UB"   ,"B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","SWIR_2","BRT"   ,"pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));
    return col_SR_L8;
#
#GET LANDSAT 7 COLLECTIONS BY PATH ROW
def fexp_landsat_7PathRow(start_date,end_date,n_path, n_row,th_cloud_cover):

    col_SR_L7 =(ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
                        .filterDate(start_date, end_date)
                        .filterMetadata('WRS_PATH', 'equals', n_path)
                        .filterMetadata('WRS_ROW', 'equals', n_row)
                        .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5' ,'ST_B6' ,'SR_B7' ,'QA_PIXEL'],
                                ["B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","BRT"   ,"SWIR_2","pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));


    return col_SR_L7;

#GET LANDSAT 5 COLLECTIONS BY PATH ROW
def fexp_landsat_5PathRow(start_date,end_date,n_path, n_row,th_cloud_cover):
    col_SR_L5 =(ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
                        .filterDate(start_date, end_date)
                        .filterMetadata('WRS_PATH', 'equals', n_path)
                        .filterMetadata('WRS_ROW', 'equals', n_row)
                        .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5' ,'ST_B6' ,'SR_B7' ,'QA_PIXEL'],
                                ["B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","BRT"   ,"SWIR_2","pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));

    return col_SR_L5;

#GET LANDSAT 7 COLLECTIONS BY COORDINATE
def fexp_landsat_7Coordinate(start_date,end_date,coordinate,th_cloud_cover):

    col_SR_L7 =(ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
                        .filterDate(start_date, end_date)
                        .filterBounds(coordinate)
                        .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5' ,'ST_B6' ,'SR_B7' ,'QA_PIXEL'],
                                ["B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","BRT"   ,"SWIR_2","pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));


    return col_SR_L7;

#GET LANDSAT 8 COLLECTIONS BY COORDINATE
def fexp_landsat_8Coordinate(start_date,end_date,coordinate,th_cloud_cover):
    col_SR_L8 =(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                        .filterDate(start_date, end_date)
                        .filterBounds(coordinate)
                        .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6' ,'SR_B7' ,'ST_B10','QA_PIXEL'],
                                ["UB"   ,"B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","SWIR_2","BRT"   ,"pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));
    return col_SR_L8;

def fexp_landsat_9Coordinate(start_date,end_date,coordinate,th_cloud_cover):
    col_SR_L8 =(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
                        .filterDate(start_date, end_date)
                        .filterBounds(coordinate)
                        .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6' ,'SR_B7' ,'ST_B10','QA_PIXEL'],
                                ["UB"   ,"B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","SWIR_2","BRT"   ,"pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));
    return col_SR_L8;
#GET LANDSAT 5 COLLECTIONS BY COORDINATE
def fexp_landsat_5Coordinate(start_date,end_date,coordinate,th_cloud_cover):
    col_SR_L5 =(ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
                        .filterDate(start_date, end_date)
                        .filterBounds(coordinate)
                        .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5' ,'ST_B6' ,'SR_B7' ,'QA_PIXEL'],
                                ["B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","BRT"   ,"SWIR_2","pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));

    return col_SR_L5;
