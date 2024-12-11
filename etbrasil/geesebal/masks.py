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

# SCALE FACTORS
# def apply_scale_factorsL8_SR(image):
#   optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
#   thermal_band = image.select('ST_B.*').multiply(0.00341802).add(149.0)
#   return image.addBands(optical_bands, None, True).addBands(thermal_band, None, True)


def apply_scale_factorsL8_SR(image):
    # Apply scaling to renamed optical bands
    optical_bands = image.select(['UB', 'B', 'GR', 'R', 'NIR', 'SWIR_1', 'SWIR_2']).multiply(0.0000275).add(-0.2)
    # Apply scaling to renamed thermal band
    thermal_band = image.select('BRT').multiply(0.00341802).add(149.0)
    
    # Add scaled bands back to image, replacing original bands
    return image.addBands(optical_bands, None, True).addBands(thermal_band, None, True)

def apply_scale_factorsL457_SR(image):
    # optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    # thermal_band = image.select('ST_B6').multiply(0.00341802).add(149.0)
    # return image.addBands(optical_bands, None, True).addBands(thermal_band, None, True)
    # Apply scaling to renamed optical bands
    optical_bands = image.select(['B', 'GR', 'R', 'NIR', 'SWIR_1', 'SWIR_2']).multiply(0.0000275).add(-0.2)
    # Apply scaling to renamed thermal band
    thermal_band = image.select('BRT').multiply(0.00341802).add(149.0)
    
    # Add scaled bands back to image, replacing original bands
    return image.addBands(optical_bands, None, True).addBands(thermal_band, None, True)

#CLOUD REMOVAL
#FUNCTION TO MASK CLOUDS IN LANDSAT 5 AND 7 FOR SURFACE REFLECTANCE

def f_cloudMaskL457_SR(image):
    final_mask = image.select('pixel_qa').bitwiseAnd(int('11111', 2)).eq(0)
    return image.updateMask(final_mask);

#FUNCTION FO MASK CLOUD IN LANDSAT 8 FOR SURFACE REFELCTANCE
def f_cloudMaskL8_SR(image):
    final_mask = image.select('pixel_qa').bitwiseAnd(int('11111', 2)).eq(0)
    return image.updateMask(final_mask);
#
#ALBEDO
#TASUMI ET AL(2008) FOR LANDSAT 5 AND 7
def f_albedoL5L7(image):
    alfa = image.expression(
      '(0.254*B1) + (0.149*B2) + (0.147*B3) + (0.311*B4) + (0.103*B5) + (0.036*B7)',{
        'B1' : image.select(['B']),
        'B2' : image.select(['GR']),
        'B3' : image.select(['R']),
        'B4' : image.select(['NIR']),
        'B5' : image.select(['SWIR_1']),
        'B7' : image.select(['SWIR_2'])
      }).rename('ALFA');

    #ADD BANDS
    return image.addBands(alfa);

#ALBEDO
#USING TASUMI ET AL. (2008) METHOD FOR LANDSAT 8
#COEFFICIENTS FROM KE ET AL. (2016)
def f_albedoL8(image):
    alfa = image.expression(
      '(0.130*B1) + (0.115*B2) + (0.143*B3) + (0.180*B4) + (0.281*B5) + (0.108*B6) + (0.042*B7)',{  #// (Ke, Im  et al 2016)
        'B1' : image.select(['UB']),
        'B2' : image.select(['B']),
        'B3' : image.select(['GR']),
        'B4' : image.select(['R']),
        'B5' : image.select(['NIR']),
        'B6' : image.select(['SWIR_1']),
        'B7' : image.select(['SWIR_2'])
      }).rename('ALFA');

    #ADD BANDS
    return image.addBands(alfa);

if __name__ == "__main__":
    f_albedoL8()
    f_albedoL5L7()
    f_cloudMaskL8_SR()
    f_cloudMaskL457_SR()
