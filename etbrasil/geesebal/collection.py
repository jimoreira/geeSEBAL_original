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
from datetime import date

#FOLDERS
from .landsatcollection import fexp_landsat_5PathRow,fexp_landsat_7PathRow, fexp_landsat_8PathRow, fexp_landsat_9PathRow
from .landsatcollection import fexp_landsat_5Coordinate,fexp_landsat_7Coordinate, fexp_landsat_8Coordinate, fexp_landsat_9Coordinate
from .masks import (apply_scale_factorsL8_SR, apply_scale_factorsL457_SR, f_cloudMaskL457_SR,f_cloudMaskL8_SR,f_albedoL5L7,f_albedoL8)
from .meteorology import get_meteorology
from .tools import (fexp_spec_ind, fexp_lst_export,fexp_radlong_up, LST_DEM_correction,
fexp_radshort_down, fexp_radlong_down, fexp_radbalance, fexp_soil_heat,fexp_sensible_heat_flux)
from .endmembers import fexp_cold_pixel, fexp_hot_pixel
from .evapotranspiration import fexp_et

#COLLECTION FUNCTION
class Collection():

    #ENDMEMBERS DEFAULT
    #ALLEN ET AL. (2013)
    def __init__(self,
                 year_i,
                 month_i,
                 day_i,
                 year_e,
                 month_e,
                 day_e,
                 cloud_cover,
                 #path,
                 #row,
                 coordinate,
                 NDVI_cold=5,
                 Ts_cold=20,
                 NDVI_hot=10,
                 Ts_hot=20):

        #INFORMATIONS
        self.coordinate=coordinate
        #self.path=path
        #self.row=row
        self.cloud_cover=cloud_cover
        self.start_date = ee.Date.fromYMD(year_i,month_i,day_i)
        self.i_date=date(year_i,month_i,day_i)
        self.end_date=date(year_e,month_e,day_e)
        self.n_search_days=self.end_date - self.i_date
        self.n_search_days=self.n_search_days.days
        self.end_date = self.start_date.advance(self.n_search_days, 'day')

        #COLLECTIONS
        # self.collection_l5=fexp_landsat_5PathRow(self.start_date, self.end_date, self.path, self.row, self.cloud_cover)
        # self.collection_l7=fexp_landsat_7PathRow(self.start_date, self.end_date, self.path, self.row, self.cloud_cover)
        # self.collection_l8=fexp_landsat_8PathRow(self.start_date, self.end_date, self.path, self.row, self.cloud_cover)
        # self.collection_l9=fexp_landsat_9PathRow(self.start_date, self.end_date, self.path, self.row, self.cloud_cover)

        self.collection_l5=fexp_landsat_5Coordinate(self.start_date, self.end_date, self.coordinate, self.cloud_cover)
        self.collection_l7=fexp_landsat_7Coordinate(self.start_date, self.end_date, self.coordinate, self.cloud_cover)
        self.collection_l8=fexp_landsat_8Coordinate(self.start_date, self.end_date, self.coordinate, self.cloud_cover)
        self.collection_l9=fexp_landsat_9Coordinate(self.start_date, self.end_date, self.coordinate, self.cloud_cover)


        #LIST OF IMAGES
        self.sceneListL5 = self.collection_l5.aggregate_array('system:index').getInfo()
        self.sceneListL7 = self.collection_l7.aggregate_array('system:index').getInfo()
        self.sceneListL8 = self.collection_l8.aggregate_array('system:index').getInfo()
        self.sceneListL9 = self.collection_l9.aggregate_array('system:index').getInfo()

        self.collection = self.collection_l5.merge(self.collection_l7).merge(self.collection_l8).merge(self.collection_l9)
        self.CollectionList=self.collection.sort("system:time_start").aggregate_array('system:index').getInfo()
        self.CollectionList_image = self.collection.aggregate_array('system:index').getInfo()
        self.count = self.collection.size().getInfo()

        #PRINT NUMBER OF SCENES
        print("Number of scenes: ", self.count)
        #print(self.collection)
        n =0
        k=0

        #====== ITERATIVE PROCESS ======#
        #FOR EACH IMAGE ON THE LIST
        #ESTIMATE ET DAILY IMAGE
        while n < self.count:
            #GET IMAGE
            self.image= self.collection.filterMetadata('system:index','equals',self.CollectionList[n]).first()
            self.image=ee.Image(self.image)

            #PRINT ID
            print(self.image.get('LANDSAT_PRODUCT_ID').getInfo())

            #GET INFORMATIONS FROM IMAGE
            self._index=self.image.get('system:index')
            self.cloud_cover=self.image.get('CLOUD_COVER')
            self.LANDSAT_ID=self.image.get('LANDSAT_PRODUCT_ID').getInfo()
            self.landsat_version=self.image.get('SPACECRAFT_ID').getInfo()
            self.sun_elevation=self.image.get('SUN_ELEVATION').getInfo()
            self.time_start=self.image.get('system:time_start')
            self._date=ee.Date(self.time_start)
            self._year=ee.Number(self._date.get('year'))
            self._month=ee.Number(self._date.get('month'))
            self._day=ee.Number(self._date.get('month'))
            self._hour=ee.Number(self._date.get('hour'))
            self._minuts = ee.Number(self._date.get('minutes'))
            self.crs = self.image.projection().crs()
            self.transform = ee.List(ee.Dictionary(ee.Algorithms.Describe(self.image.projection())).get('transform'))
            self.date_string=self._date.format('YYYY-MM-dd').getInfo()

            #ENDMEMBERS
            self.p_top_NDVI=ee.Number(NDVI_cold)
            self.p_coldest_Ts=ee.Number(Ts_cold)
            self.p_lowest_NDVI=ee.Number(NDVI_hot)
            self.p_hottest_Ts=ee.Number(Ts_hot)


            #MAKS
            if self.landsat_version == 'LANDSAT_5':
                # self.image = self.image.select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5' ,'ST_B6' ,'SR_B7' ,'QA_PIXEL'],
                #                                ["B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","BRT"   ,"SWIR_2","pixel_qa"])
                #self.image_toa=ee.Image('LANDSAT/LT05/C02/T1_TOA/'+ self._index.getInfo())
                #self.image_toa=ee.Image('LANDSAT/LT05/C02/T1_TOA/'+ self.CollectionList[n][4:])
            
                #GET CALIBRATED RADIANCE
                #self.col_rad = ee.Algorithms.Landsat.calibratedRadiance(self.image_toa);
                #self.col_rad = self.image.addBands(self.col_rad.select(['B6'],["T_RAD"]))

                #APPLY SCALE FACTORS
                self.image=ee.ImageCollection(self.image).map(apply_scale_factorsL457_SR)

                #CLOUD REMOTION
                self.image=ee.ImageCollection(self.image).map(f_cloudMaskL457_SR)

                #ALBEDO TASUMI ET AL. (2008)
                self.image=self.image.map(f_albedoL5L7)

            elif self.landsat_version == 'LANDSAT_7':
                # self.image = self.image.select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5' ,'ST_B6' ,'SR_B7' ,'QA_PIXEL'],
                #                                ["B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","BRT"   ,"SWIR_2","pixel_qa"])
                #self.image_toa=ee.Image('LANDSAT/LE07/C02/T1_TOA/'+ self.CollectionList[n][4:])

                #GET CALIBRATED RADIANCE
                #self.col_rad = ee.Algorithms.Landsat.calibratedRadiance(self.image_toa);
                #self.col_rad = self.image.addBands(self.col_rad.select(['B6_VCID_1'],["T_RAD"]))

                #APPLY SCALE FACTORS
                self.image=ee.ImageCollection(self.image).map(apply_scale_factorsL457_SR)
                #CLOUD REMOTION
                self.image=ee.ImageCollection(self.image).map(f_cloudMaskL457_SR)

                #ALBEDO TASUMI ET AL. (2008)
                self.image=self.image.map(f_albedoL5L7)

            elif self.landsat_version == 'LANDSAT_8':
                # self.image = self.image.select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6' ,'SR_B7' ,'ST_B10','QA_PIXEL'],
                #                               ["UB"   ,"B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","SWIR_2","BRT"   ,"pixel_qa"])
                # self.image_toa=ee.Image('LANDSAT/LC08/C02/T1_TOA/'+self._index.getInfo())
                # #
                #self.image_toa=ee.Image('LANDSAT/LC08/C02/T1_TOA/'+self.CollectionList[n][2:])

                
                #GET CALIBRATED RADIANCE
                #self.col_rad = ee.Algorithms.Landsat.calibratedRadiance(self.image_toa)
                #self.col_rad = self.image.addBands(self.col_rad.select(['B10'],["T_RAD"]))
                
                #APPLY SCALE FACTORS
                self.image=ee.ImageCollection(self.image).map(apply_scale_factorsL8_SR)
                #self.image = self.image.first()
                    #CLOUD REMOTION
                self.image=ee.ImageCollection(self.image).map(f_cloudMaskL8_SR)

                #ALBEDO TASUMI ET AL. (2008) METHOD WITH KE ET AL. (2016) COEFFICIENTS
                self.image=self.image.map(f_albedoL8)
            
            elif self.landsat_version == 'LANDSAT_9':
                # self.image = self.image.select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6' ,'SR_B7' ,'ST_B10','QA_PIXEL'],
                #                               ["UB"   ,"B"    ,"GR"   ,"R"    ,"NIR"  ,"SWIR_1","SWIR_2","BRT"   ,"pixel_qa"])
                # self.image_toa=ee.Image('LANDSAT/LC08/C02/T1_TOA/'+self._index.getInfo())
                # #
                #self.image_toa=ee.Image('LANDSAT/LC08/C02/T1_TOA/'+self.CollectionList[n][2:])

                
                #GET CALIBRATED RADIANCE
                #self.col_rad = ee.Algorithms.Landsat.calibratedRadiance(self.image_toa)
                #self.col_rad = self.image.addBands(self.col_rad.select(['B10'],["T_RAD"]))
                
                #APPLY SCALE FACTORS
                self.image=ee.ImageCollection(self.image).map(apply_scale_factorsL8_SR)
                #self.image = self.image.first()
                    #CLOUD REMOTION
                self.image=ee.ImageCollection(self.image).map(f_cloudMaskL8_SR)

                #ALBEDO TASUMI ET AL. (2008) METHOD WITH KE ET AL. (2016) COEFFICIENTS
                self.image=self.image.map(f_albedoL8)
            else: 
                raise Exception('ingestion failed.')

            #GEOMETRY
            self.geometryReducer=self.image.geometry().bounds().getInfo()
            self.geometry_download=self.geometryReducer['coordinates']
            self.camada_clip=self.image.select('BRT').first()

            #METEOROLOGY PARAMETERS
            col_meteorology= get_meteorology(self.image,self.time_start)

            #AIR TEMPERATURE [C]
            self.T_air = col_meteorology.select('AirT_G')

            #WIND SPEED [M S-1]
            self.ux= col_meteorology.select('ux_G')

            #RELATIVE HUMIDITY (%)
            self.UR = col_meteorology.select('RH_G')

            #NET RADIATION 24H [W M-2]
            self.Rn24hobs = col_meteorology.select('Rn24h_G')

            #SRTM DATA ELEVATION
            SRTM_ELEVATION ='USGS/SRTMGL1_003' # SRTM Data Elevation
            self.srtm = ee.Image(SRTM_ELEVATION).clip(self.geometryReducer)
            self.z_alt = self.srtm.select('elevation')

            #TO AVOID ERRORS DURING THE PROCESS
            try:
                #GET IMAGE
                self.image=self.image.first()

                #SPECTRAL IMAGES (NDVI, EVI, SAVI, LAI, T_LST, e_0, e_NB, long, lat)
                self.image=fexp_spec_ind(self.image)

                #LAND SURFACE TEMPERATURE
                #self.image =fexp_lst_export(self.image,self.col_rad,self.landsat_version,self.geometryReducer)
                self.image=LST_DEM_correction(self.image, self.z_alt, self.T_air, self.UR,self.sun_elevation,self._hour,self._minuts)

                #COLD PIXEL
                self.d_cold_pixel=fexp_cold_pixel(self.image, self.geometryReducer, self.p_top_NDVI, self.p_coldest_Ts)

                #COLD PIXEL NUMBER
                self.n_Ts_cold = ee.Number(self.d_cold_pixel.get('temp').getInfo())
                
                #INSTANTANEOUS OUTGOING LONG-WAVE RADIATION [W M-2]
                self.image=fexp_radlong_up(self.image)

                #INSTANTANEOUS INCOMING SHORT-WAVE RADIATION [W M-2]
                self.image=fexp_radshort_down(self.image,self.z_alt,self.T_air,self.UR, self.sun_elevation)

                #INSTANTANEOUS INCOMING LONGWAVE RADIATION [W M-2]
                self.image=fexp_radlong_down(self.image, self.n_Ts_cold)

                #INSTANTANEOUS NET RADIATON BALANCE [W M-2]
                self.image=fexp_radbalance(self.image)

                #SOIL HEAT FLUX (G) [W M-2]
                self.image=fexp_soil_heat(self.image)

                #HOT PIXEL
                self.d_hot_pixel=fexp_hot_pixel(self.image, self.geometryReducer,self.p_lowest_NDVI, self.p_hottest_Ts)
                #SENSIBLE HEAT FLUX (H) [W M-2]
                self.image=fexp_sensible_heat_flux(self.image, self.ux, self.UR,self.Rn24hobs,self.n_Ts_cold,
                                                    self.d_hot_pixel, self.date_string,self.geometryReducer)

                #DAILY EVAPOTRANSPIRATION (ET_24H) [MM DAY-1]
                self.image=fexp_et(self.image,self.Rn24hobs)


                self.NAME_FINAL=self.LANDSAT_ID[:5]+self.LANDSAT_ID[10:17]+self.LANDSAT_ID[17:25]
                
                # Select the ET_24h band and give it a custom name
                self.ET_daily = self.image.select(['ET_24h'], [self.NAME_FINAL])

                # Check for valid data (not NaN) in the selected band
                stats = self.ET_daily.reduceRegion(
                    reducer=ee.Reducer.minMax(),#
                    geometry=self.image.geometry(),
                    scale=30,  # Adjust based on image resolution
                    bestEffort=True
                ).getInfo()

                # Ensure valid min/max values before adding
                if stats[f'{self.NAME_FINAL}_min'] is not None and stats[f'{self.NAME_FINAL}_max'] is not None:
                    if k == 0:
                        # Initialize the collection with the first valid band
                        self.Collection_ET = self.ET_daily
                    else:
                        # Add the valid band to the existing collection
                        self.Collection_ET = self.Collection_ET.addBands(self.ET_daily)

                    #print(f"Added ET band for image {n}: {self.NAME_FINAL}, collection now has {self.Collection_ET.bandNames().getInfo()} bands.")
                    k += 1  # Increment only if successfully added a valid band
                else:
                    print(f"Skipping image {n} due to NaN values in statistics.")


            except Exception as e:
                # Log the error and skip the problematic image
                print(f'Error processing image {n}: {e}')

            # Move to the next image in the list
            n += 1
            
        # Print final band collection after all iterations
        if k > 0:
            print(f"Final collection has {self.Collection_ET.bandNames().getInfo()} bands.")
        else:
            print("No valid ET bands were added to the collection.")

    def get_collection(self):
        return self.Collection_ET