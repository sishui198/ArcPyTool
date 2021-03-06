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
    level=logging.DEBUG,  # 定义输出到文件的log级别，大于此级别的都被输出
    format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',  # 定义输出log的格式
    datefmt='%Y-%m-%d %A %H:%M:%S',  # 时间
    filename= LogPathName,  # log文件名
    filemode='w')  # 写入模式“w”或“a”
# Define a Handler and set a format which output to console
console = logging.StreamHandler()  # 定义console handler
console.setLevel(logging.INFO)  # 定义该handler级别
formatter = logging.Formatter('%(asctime)s  %(filename)s : %(levelname)s  %(message)s')  # 定义该handler格式
console.setFormatter(formatter)
# Create an instance
logging.getLogger().addHandler(console)  # 实例化添加handler
# 输出日志级别
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
# 点集{'管线点预编号': 对应表格行}(埋深变为最低点)
points = {}
connectid = 1
flag = False

# 相关列的下标变量
# 预编号列与连接点号
name = 0
toname = 1
# 埋设方式
mode = 2
# 管线材料
material = 3
# 管径mm
diameter = 4
# 特征
prop = 5
# 附属物
attach = 6
# 平面坐标x y
x = 7
y = 8
# 地面高程
ground = 9
# 埋深
depth = 12
# 电缆数
elenum = 13
# 管孔排列
collocate = 14
# 电力电压
voltage = 15
# 备注
remark = 16
# 管线类型
pipetype = 17

# 添加一行 工作表、第n行、[内容数组]
def addRow(sheet,row,array):
    i = 0
    for item in array:
        sheet.write(row,i,item)
        i = i+1

# 检测埋深数据是否为空或者是否为float类型 计算返回改点高程 不合法点高程为0
def CheckElevation(arg):
    try:
        return float(arg[ground].value) - float(arg[depth].value)
    except Exception as e:
        # print(e.message + u"\n不合法点高程为0")
        return 0

# 检测管径数据是否合法 不合法默认半径为0.1米 t = 0时为宽 t = 1时为高
def CheckDiameter(diameter, t):
    try:
        return float(diameter)/2000.0
    except Exception as e:
        try:
            return float(diameter.split('X')[t])/2000.0
        except Exception as e:
            # print(e.message + u"\n未知数据默认半径0.1米")
            return 0.1

# 返回当前管点最大的埋深管线埋深 
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
                # print(e.message + u"\n未知数据默认埋深为0")
                return 0
            else:
                return float(rowdepth)
        else:
            return float(nowdepth)
    else:
        return t2 if t1 < t2 else t1

# 管点对应管线ID row当前遍历的行
def AddConnectTable(endptA, endptB ,row):
    # 坐标信息
    startx = row[x].value
    starty = row[y].value
    lineID = endptA + '_' + endptB
    startz = CheckElevation(row)
    # 相关属性
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

# 管点类型数组
Pointtype = [u"电信手孔", u"电信人孔", u"检查井" , u"未知井", u"阀门井", u"检修井", u"雨篦", u"路灯", u"排泥井", u"消防栓", u"消火栓"]
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
            # 地面高程
            pth = value[ground].value
            # 最低点高程
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
# 添加表头
addRow(connectsheet,0,["id", "x", "y", "z", "startpt", "endpt", "mode", "material", "width", "heigh", "electric", "collocate", "voltage", "pipelinetype", "projectseq"])
addRow(pointsheet,0,["id", "x", "y", "z", "attach", "prop", "pipelinetype"])
addRow(pointsheet2,0,["id", "x", "y", "z", "attach", "prop", "pipelinetype", "buf"])
addRow(allpointssheet,0,["id", "x", "y", "z", "attach", "prop", "ground", "pipelinetype", "projectseq"])

for row in rows:
    start = row[name].value
    # if u"管线类型" in start:
    #     pipetype = start[5:]
    end = row[toname].value
    # 找管线点预编号一行
    if not flag:
        if start != u"管线点\n预编号":
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
            # 记录当前正在判断的起始点 check in start point of the now row
            nowrow = row
            points[start] = row
            # print(nowrow[0].value)
            #终点已存在点集内
            if end in points:
                AddConnectTable(end, start, row)
                # print(u"%s与当前起始点%s相连" % (end,start))
            else:
                AddConnectTable(start, end, row)
                # print(u"跳过%s" % end)
            points[nowrow[0].value][depth].value = CheckDepth(nowrow[depth].value, row[depth].value)
        # 起始点位置为空 即判断终点是否在点集中
        else:
            # 将管井点最低高程管的埋深更新至点集中
            points[nowrow[0].value][depth].value = CheckDepth(nowrow[depth].value, row[depth].value)
            if end in points:
                AddConnectTable(end, nowrow[0].value, row)
                # print(u"%s与当前起始点%s相连" % (end,nowrow[0].value))
            else:
                AddConnectTable(nowrow[0].value, end, row)
                # print(u"跳过%s" % end)

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
    # 生成三维管线
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

    # 生成三维管点
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
    
    # 其他管点
    logging.info('create point23d')
    arcpy.MakeXYEventLayer_management(point2_table, "x", "y", "templayer",spatial_reference = inputSR, in_z_field = "z")
    arcpy.FeatureClassToFeatureClass_conversion(in_features = "templayer",out_path = "in_memory", out_name = "tempPoint")
    arcpy.Buffer3D_3d("in_memory" + "\\" + "tempPoint", Point23dName, 'buf', 'STRAIGHT', 30)
    logging.info('Buffer3D_3d create point23d')
    arcpy.Delete_management("in_memory")

    # 输出点集
    arcpy.MakeXYEventLayer_management(allpoints_table, "x", "y", "templayer",spatial_reference = inputSR, in_z_field = "z")
    arcpy.FeatureClassToFeatureClass_conversion(in_features = "templayer",out_path = outputFile, out_name = PointFeatureName)
    logging.info('point shp file')

except arcpy.ExecuteError:
    errorMsgs = arcpy.GetMessages(2)
    logging.error(str(errorMsgs))
    arcpy.AddError(str(errorMsgs))
    arcpy.AddMessage("Failed!")
    pass