#!usr/bin/python
# -*- coding: gbk -*-
import arcpy
import re
import xlrd
import xlwt
import logging
import sys
# arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = "UNQUALIFIED"

inputPipeTable = r'E:\ArcPyscript/dill/a.xls'
outputFile = r"E:\ArcPyscript\dill"
PipeFeatureName = r"pipe.shp"
PointFeatureName = r"point.shp"
GDBworkspace = r"E:\ArcPyscript/dill/test.gdb"
SDEworkspace = r"C:\Users\Mr_Yin\AppData\Roaming\ESRI\Desktop10.6\ArcCatalog\szgis.sde"
outTempTable = r"E:\ArcPyscript/dill/temp.xls"
LogPathName = r"./sblog.log"
projectSequence = r"abc123"

# inputPipeTable = arcpy.GetParameterAsText(0)
# outputFile = arcpy.GetParameterAsText(1)
# PipeFeatureName = arcpy.GetParameterAsText(2)
# PointFeatureName = arcpy.GetParameterAsText(3)
# GDBworkspace = arcpy.GetParameterAsText(4)
# outTempTable = arcpy.GetParameterAsText(5)
# LogPathName = arcpy.GetParameterAsText(6)
# SDEworkspace = arcpy.GetParameterAsText(7)
# projectSequence = arcpy.GetParameterAsText(8)

# Define a Handler and set a format which output to file
logging.basicConfig(
    level=logging.DEBUG,  # ����������ļ���log���𣬴��ڴ˼���Ķ������
    format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',  # �������log�ĸ�ʽ
    datefmt='%Y-%m-%d %A %H:%M:%S',  # ʱ��
    filename= LogPathName,  # log�ļ���
    filemode='w')  # д��ģʽ��w����a��
# Define a Handler and set a format which output to console
console = logging.StreamHandler()  # ����console handler
console.setLevel(logging.INFO)  # �����handler����
formatter = logging.Formatter('%(asctime)s  %(filename)s : %(levelname)s  %(message)s')  # �����handler��ʽ
console.setFormatter(formatter)
# Create an instance
logging.getLogger().addHandler(console)  # ʵ�������handler
# �����־����
# Print information             
# logging.debug('logger debug message')
# logging.info('logger info message')
# logging.warning('logger warning message')
# logging.error('logger error message')
# logging.critical('logger critical message')


arcpy.env.workspace = GDBworkspace
sheet =  xlrd.open_workbook(inputPipeTable).sheet_by_index(0)
rows = sheet.get_rows()
tempExcel = xlwt.Workbook()
connectsheet = tempExcel.add_sheet('connect')
pointsheet = tempExcel.add_sheet('point')
pointsheet2 = tempExcel.add_sheet('point2')
allpointssheet = tempExcel.add_sheet('allpoints')
# �㼯{'���ߵ�Ԥ���': ��Ӧ�����}(�����Ϊ��͵�)
points = {}
connectid = 1
flag = False

# ����е��±����
# Ԥ����������ӵ��
name = 0
toname = 1
# ���跽ʽ
mode = 2
# ���߲���
material = 3
# �ܾ�mm
diameter = 4
# ����
prop = 5
# ������
attach = 6
# ƽ������x y
x = 7
y = 8
# ����߳�
ground = 9
# ����
depth = 12
# ������
elenum = 13
# �ܿ�����
collocate = 14
# ������ѹ
voltage = 15
# ��ע
remark = 16
# ��������
pipetype = 17

# ���һ�� ��������n�С�[��������]
def addRow(sheet,row,array):
    i = 0
    for item in array:
        sheet.write(row,i,item)
        i = i+1

# ������������Ƿ�Ϊ�ջ����Ƿ�Ϊfloat���� ���㷵�ظĵ�߳� ���Ϸ���߳�Ϊ0
def CheckElevation(arg):
    try:
        return float(arg[ground].value) - float(arg[depth].value)
    except Exception as e:
        # print(e.message + u"\n���Ϸ���߳�Ϊ0")
        return 0

# ���ܾ������Ƿ�Ϸ� ���Ϸ�Ĭ�ϰ뾶Ϊ0.1�� t = 0ʱΪ�� t = 1ʱΪ��
def CheckDiameter(diameter, t):
    try:
        return float(diameter)/2000.0
    except Exception as e:
        try:
            return float(diameter.split('X')[t])/2000.0
        except Exception as e:
            # print(e.message + u"\nδ֪����Ĭ�ϰ뾶0.1��")
            return 0.1

# ���ص�ǰ�ܵ���������������� 
def CheckDepth(nowdepth, rowdepth):
    try:
        t1 = float(nowdepth)
        t2 = float(rowdepth)
    except Exception as e:
        try:
            float(nowdepth)
        except Exception as e:
            try:
                float(rowdepth)
            except Exception as e:
                # print(e.message + u"\nδ֪����Ĭ������Ϊ0")
                return 0
            else:
                return float(rowdepth)
        else:
            return float(nowdepth)
    else:
        return t2 if t1 < t2 else t1

# �ܵ��Ӧ����ID row��ǰ��������
def AddConnectTable(endptA, endptB ,row):
    # ������Ϣ
    startx = row[x].value
    starty = row[y].value
    lineID = endptA + '_' + endptB
    startz = CheckElevation(row)
    # �������
    mod = row[mode].value
    mat = row[material].value
    wid = CheckDiameter(row[diameter].value, 0)
    hei = CheckDiameter(row[diameter].value, 1)
    ele = row[elenum].value
    col = row[collocate].value
    vol = row[voltage].value
    pipelinetype = row[pipetype].value
    global connectid
    addRow(connectsheet,connectid,[lineID, startx, starty, startz, endptA, endptB, mod, mat, wid, hei, ele, col, vol, pipelinetype, projectSequence])
    connectid += 1

# �ܵ���������
Pointtype = [u"�����ֿ�", u"�����˿�", u"��龮" , u"δ֪��", u"���ž�", u"���޾�", u"����", u"·��", u"���ྮ", u"����˨", u"����˨"]
def AddPointsTable(points):
    pt = 1
    pointid = 1
    pointid2 = 1
    for key, value in points.items():
        ptnum = key
        ptx = value[x].value
        pty = value[y].value
        ptprop = value[prop].value
        ptattach = value[attach].value
        ptz = value[ground].value - value[depth].value
        gro = value[ground].value
        pipelinetype = value[pipetype].value
        
        addRow(allpointssheet, pt, [ptnum, ptx, pty, ptz, ptattach, ptprop, gro, pipelinetype, projectSequence])
        pt += 1
        if value[attach].value in Pointtype:
            # ����߳�
            pth = value[ground].value
            # ��͵�߳�
            ptz = pth - value[depth].value - CheckDiameter(value[diameter].value, 0)
            addRow(pointsheet, pointid, [ptnum, ptx, pty, ptz, ptattach, ptprop, pipelinetype])
            addRow(pointsheet, pointid+1, [ptnum, ptx, pty, pth, ptattach, ptprop ,pipelinetype])
            pointid += 2
        else:
            ptz = value[ground].value - value[depth].value
            buf = CheckDiameter(value[diameter].value, 0) + 0.1
            addRow(pointsheet2, pointid2, [ptnum, ptx, pty, ptz, ptattach, ptprop, pipelinetype, buf])
            pointid2 += 1
            pass
# ��ӱ�ͷ
addRow(connectsheet,0,["id", "x", "y", "z", "startpt", "endpt", "mode", "material", "width", "heigh", "electric", "collocate", "voltage", "pipelinetype", "projectseq"])
addRow(pointsheet,0,["id", "x", "y", "z", "attach", "prop", "pipelinetype"])
addRow(pointsheet2,0,["id", "x", "y", "z", "attach", "prop", "pipelinetype", "buf"])
addRow(allpointssheet,0,["id", "x", "y", "z", "attach", "prop", "ground", "pipelinetype", "projectseq"])

for row in rows:
    start = row[name].value
    # if u"��������" in start:
    #     pipetype = start[5:]
    end = row[toname].value
    # �ҹ��ߵ�Ԥ���һ��
    if not flag:
        if start != u"���ߵ�\nԤ���":
            continue
        else:
            flag = True
            continue
    else:
        # skips when meet two blank cell
        if(start == u'' and end == u''):
            continue
        # if found start point 
        if start != '':
            # ��¼��ǰ�����жϵ���ʼ�� check in start point of the now row
            nowrow = row
            points[start] = row
            # print(nowrow[0].value)
            #�յ��Ѵ��ڵ㼯��
            if end in points:
                AddConnectTable(end, start, row)
                # print(u"%s�뵱ǰ��ʼ��%s����" % (end,start))
            else:
                AddConnectTable(start, end, row)
                # print(u"����%s" % end)
            points[nowrow[0].value][depth].value = CheckDepth(nowrow[depth].value, row[depth].value)
        # ��ʼ��λ��Ϊ�� ���ж��յ��Ƿ��ڵ㼯��
        else:
            # ���ܾ�����͸̹߳ܵ�����������㼯��
            points[nowrow[0].value][depth].value = CheckDepth(nowrow[depth].value, row[depth].value)
            if end in points:
                AddConnectTable(end, nowrow[0].value, row)
                # print(u"%s�뵱ǰ��ʼ��%s����" % (end,nowrow[0].value))
            else:
                AddConnectTable(nowrow[0].value, end, row)
                # print(u"����%s" % end)

AddPointsTable(points)
logging.info('Already created temp.xls')
tempExcel.save(outTempTable)
connect_table = GDBworkspace + "\\" + connectsheet.name
point_table = GDBworkspace + "\\" + pointsheet.name
point2_table = GDBworkspace + "\\" + pointsheet2.name
allpoints_table = GDBworkspace + "\\" + allpointssheet.name
PipeName = SDEworkspace + "\\" + 'pipe3d_test'
GDBPipeName = GDBworkspace + "\\" + 'pipe3d'
Point3dName = GDBworkspace + "\\" + 'point3d'
Point23dName = GDBworkspace + "\\" + 'point23d'

# inputSR = r"GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;0.001;0.001;IsHighPrecision"
inputSR = r"PROJCS['WGS_1984_Web_Mercator_Auxiliary_Sphere',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator_Auxiliary_Sphere'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],PARAMETER['Auxiliary_Sphere_Type',0.0],UNIT['Meter',1.0]]"
try:
    # ������ά����
    arcpy.ExcelToTable_conversion(Input_Excel_File = outTempTable, Output_Table = connectsheet.name, Sheet = connectsheet.name)
    arcpy.ExcelToTable_conversion(Input_Excel_File = outTempTable, Output_Table = pointsheet.name, Sheet = pointsheet.name)
    arcpy.ExcelToTable_conversion(Input_Excel_File = outTempTable, Output_Table = pointsheet2.name, Sheet = pointsheet2.name)
    arcpy.ExcelToTable_conversion(Input_Excel_File = outTempTable, Output_Table = allpointssheet.name, Sheet = allpointssheet.name)
    arcpy.MakeXYEventLayer_management(connect_table, "x", "y", "templayer",spatial_reference = inputSR, in_z_field = "z")
    logging.info('MakeXYEventLayer_management')
    
    arcpy.FeatureClassToFeatureClass_conversion(in_features = "templayer",out_path = "in_memory", out_name = "tempPoint")
    arcpy.PointsToLine_management(Input_Features = "in_memory"+ "\\" + "tempPoint", Output_Feature_Class = "in_memory" + "\\" + "resultLine", Line_Field = "id")
    arcpy.MakeFeatureLayer_management("in_memory" + "\\" + "resultLine" , "layer")
    arcpy.AddJoin_management("layer", "id", connect_table, "id")
    logging.info('AddJoin_management')
    arcpy.FeatureClassToFeatureClass_conversion("layer", out_path = outputFile, out_name = PipeFeatureName)
    logging.info('Buffer3D_3d')
    arcpy.Buffer3D_3d(outputFile + "\\" + PipeFeatureName, GDBPipeName, 'width', 'STRAIGHT', 30)
    logging.info('Append pipeline3d data')
    arcpy.Append_management(inputs = GDBPipeName, target = PipeName)
    arcpy.Delete_management("in_memory")

    # ������ά�ܵ�
    logging.info('create point3d')
    arcpy.MakeXYEventLayer_management(point_table, "x", "y", "templayer",spatial_reference = inputSR, in_z_field = "z")
    arcpy.FeatureClassToFeatureClass_conversion(in_features = "templayer",out_path = "in_memory", out_name = "tempPoint")
    logging.info('FeatureClassToFeatureClass_conversion')    
    arcpy.PointsToLine_management(Input_Features = "in_memory"+ "\\" + "tempPoint", Output_Feature_Class = "in_memory" + "\\" + "resultLine", Line_Field = "id")

    arcpy.MakeFeatureLayer_management("in_memory" + "\\" + "resultLine" , "layer")
    arcpy.AddJoin_management("layer", "id", point_table, "id")
    logging.info('AddJoin_management')
    arcpy.FeatureClassToFeatureClass_conversion("layer", out_path = "in_memory", out_name = "temppipepoint")

    arcpy.Buffer3D_3d("in_memory" + "\\" + "temppipepoint", Point3dName, '0.5 METERS', 'STRAIGHT', 30)
    logging.info('Buffer3D_3d')
    arcpy.Delete_management("in_memory")
    
    # �����ܵ�
    logging.info('create point23d')
    arcpy.MakeXYEventLayer_management(point2_table, "x", "y", "templayer",spatial_reference = inputSR, in_z_field = "z")
    arcpy.FeatureClassToFeatureClass_conversion(in_features = "templayer",out_path = "in_memory", out_name = "tempPoint")
    arcpy.Buffer3D_3d("in_memory" + "\\" + "tempPoint", Point23dName, 'buf', 'STRAIGHT', 30)
    logging.info('Buffer3D_3d create point23d')
    arcpy.Delete_management("in_memory")

    # ����㼯
    arcpy.MakeXYEventLayer_management(allpoints_table, "x", "y", "templayer",spatial_reference = inputSR, in_z_field = "z")
    arcpy.FeatureClassToFeatureClass_conversion(in_features = "templayer",out_path = outputFile, out_name = PointFeatureName)
    logging.info('point shp file')

except arcpy.ExecuteError:
    errorMsgs = arcpy.GetMessages(2)
    logging.error(str(errorMsgs))
    arcpy.AddError(str(errorMsgs))
    arcpy.AddMessage("Failed!")
    pass