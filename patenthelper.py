import urllib2, os, zipfile, time, shelve, json
from lxml import etree

with open('zipfilenames.dct') as f:
    filenames = json.load(f)

class Patent(object):
    def __init__(self,patnum,classes,citing,title,assignee=None):
        self.patnum = patnum
        self.classes = set(classes)
        self.citing = set(citing)
        self.title = title
        if assignee:
            self.assignee = assignee


class PatentSearch(object):
    def __init__(self,num):
        self.s_shelf = 'search_shelf_%i.shlf'%num
        self.patents = set([])
        self.classifications = set([])
        self.assignees = set([])
        
        self.candidates = {}
        self.ignored = set([])
        
    def add_patent(self,patent):
        self.patents.add(patent)
        
    def add_classification(self, classification):
        self.classifications.add(classification)
        
    def num_rel_classes(self,patent):
        return len(patent.classes.intersection(self.classifications))


def xmlSplitter(data,separator=lambda x: x.startswith('<?xml')):
  buff = []
  for line in data:
    if separator(line):
      if buff:
        yield ''.join(buff)
        buff[:] = []
    buff.append(line)
  yield ''.join(buff)

def first(seq,default=None):
  '''Return the first item from sequence, seq or the default(None) value'''
  for item in seq:
    return item
  return default

def nat_class(doc):
    clanat = doc.findall('classification-national')[0]
    natcla = []
    for cla in clanat[1:]:
        natcla.append(cla.text.strip())
    return natcla

def nat_class04(doc):
    clanat = doc.findall('B500')[0].findall('B520')[0].findall('B521')[0].findtext('PDAT')
    natcla = [clanat]
    for cla in doc.findall('B500')[0].findall('B520')[0].findall('B522'):
        natcla.append(cla.findtext('PDAT').strip())
    return natcla

def patnum(doc,subdoc):
    did = subdoc.findall('document-id')[0]
    dc = did.findtext('country')
    dn = did.findtext('doc-number').lstrip('0')
    pid = dc+dn
    return pid

def own_num(doc):
    return patnum(doc,doc.findall('publication-reference')[0])

def own_num04(doc):
    did = doc.findall('B100')[0]
    dc = did.findall('B190')[0].findtext('PDAT')
    dn = did.findall('B110')[0].findall('DNUM')[0].findtext('PDAT')
    pid = dc + dn
    return pid

def citations(doc):
    citing = []
    try:
        cits = doc.findall('references-cited')[0]
        for cit in cits:
            for pc in cit.findall('patcit'):
                citing.append(patnum(cit,pc))
    except: pass
    try:
        cits = doc.findall('us-references-cited')[0]
        for cit in cits:
            for pc in cit.findall('patcit'):
                citing.append(patnum(cit,pc))
    except: pass
    return citing

def citations04(doc):
    citing = []
    try:
        cits = doc.findall('B500')[0].findall('B560')[0].findall('B561')
        for cit in cits:
            citing.append(cit.findall('PCIT')[0].findall('DOC')[0].findall('DNUM')[0].findtext('PDAT'))
    except: pass
    return citing    

def title(doc):
    return doc.findtext('invention-title')

def title04(doc):
    return doc.findall('B500')[0].findall('B540')[0].findall('STEXT')[0].findtext('PDAT')

def process_bulk_data(year):
    t_zero = time.time()
    shelf_name = 'patents%s.shlf'%year
    f = shelve.open(shelf_name,'c')
    for filename in filenames[year]:
        #year = filename[4:8]
        datasrc = 'http://commondatastorage.googleapis.com/patents/grantbib/{}/{}'.format(year,filename)
    
        if not os.path.exists(filename):
            with open(filename,'wb') as file_write:
                r = urllib2.urlopen(datasrc)
                file_write.write(r.read())
    
        zf = zipfile.ZipFile(filename)
        xml_file = first([ x for x in zf.namelist() if x.endswith('.xml')])
        assert xml_file is not None

        for item in xmlSplitter(zf.open(xml_file)):
            doc = etree.XML(item).findall('us-bibliographic-data-grant')[0]
            f[own_num(doc)]=Patent(own_num(doc),nat_class(doc),citations(doc),title(doc))
        print int(time.time()-t_zero),
    f.close()
    print '!'

def process_bulk_data04(year):
    t_zero = time.time()
    shelf_name = 'patents%s.shlf'%year
    f = shelve.open(shelf_name,'c')
    for filename in filenames[year]:
        #year = filename[4:8]
        datasrc = 'http://commondatastorage.googleapis.com/patents/grantbib/{}/{}'.format(year,filename)
    
        if not os.path.exists(filename):
            with open(filename,'wb') as file_write:
                r = urllib2.urlopen(datasrc)
                file_write.write(r.read())
    
        zf = zipfile.ZipFile(filename)
        xml_file = first([ x for x in zf.namelist() if x.endswith('.xml')])
        assert xml_file is not None

        for item in xmlSplitter(zf.open(xml_file)):
            p = etree.XMLParser(resolve_entities=False)
            doc = etree.XML(item,parser=p).findall('SDOBI')[0]
            f[own_num04(doc)]=Patent(own_num04(doc),nat_class04(doc),citations04(doc),title04(doc))
        print int(time.time()-t_zero),
    f.close()
    print '!'

def process_one_week(filename):
    t_zero = time.time()
    year = filename[4:8]
    datasrc = 'http://commondatastorage.googleapis.com/patents/grantbib/{}/{}'.format(year,filename)
    shelf_name = 'patents%s.shlf'%year
    f = shelve.open(shelf_name,'c')

    if not os.path.exists(filename):
        with open(filename,'wb') as file_write:
            r = urllib2.urlopen(datasrc)
            file_write.write(r.read())
    
    zf = zipfile.ZipFile(filename)
    xml_file = first([ x for x in zf.namelist() if x.endswith('.xml')])
    assert xml_file is not None

    for item in xmlSplitter(zf.open(xml_file)):
        doc = etree.XML(item).findall('us-bibliographic-data-grant')[0]
        f[own_num(doc)]=Patent(own_num(doc),nat_class(doc),citations(doc),title(doc))
    f.close()
    print int(time.time()-t_zero),'!'

def download_week_zip(filename):
    year = filename[3:7]
    datasrc = 'http://commondatastorage.googleapis.com/patents/grantbib/{}/{}'.format(year,filename)
    if not os.path.exists(filename):
        with open(filename,'wb') as file_write:
            r = urllib2.urlopen(datasrc)
            file_write.write(r.read())


filenames = {}
filenames[2001] = [
    'pgb20010102_wk01.zip','pgb20010109_wk02.zip','pgb20010116_wk03.zip','pgb20010123_wk04.zip',
    'pgb20010130_wk05.zip','pgb20010206_wk06.zip','pgb20010213_wk07.zip','pgb20010220_wk08.zip',
    'pgb20010227_wk09.zip','pgb20010306_wk10.zip','pgb20010313_wk11.zip','pgb20010320_wk12.zip',
    'pgb20010327_wk13.zip','pgb20010403_wk14.zip','pgb20010410_wk15.zip','pgb20010417_wk16.zip',
    'pgb20010424_wk17.zip','pgb20010501_wk18.zip','pgb20010508_wk19.zip','pgb20010515_wk20.zip',
    'pgb20010522_wk21.zip','pgb20010529_wk22.zip','pgb20010605_wk23.zip','pgb20010612_wk24.zip',
    'pgb20010619_wk25.zip','pgb20010626_wk26.zip','pgb20010703_wk27.zip','pgb20010710_wk28.zip',
    'pgb20010717_wk29.zip','pgb20010724_wk30.zip','pgb20010731_wk31.zip','pgb20010807_wk32.zip',
    'pgb20010814_wk33.zip','pgb20010821_wk34.zip','pgb20010828_wk35.zip','pgb20010904_wk36.zip',
    'pgb20010911_wk37.zip','pgb20010918_wk38.zip','pgb20010925_wk39.zip','pgb20011002_wk40.zip',
    'pgb20011009_wk41.zip','pgb20011016_wk42.zip','pgb20011023_wk43.zip','pgb20011030_wk44.zip',
    'pgb20011106_wk45.zip','pgb20011113_wk46.zip','pgb20011120_wk47.zip','pgb20011127_wk48.zip',
    'pgb20011204_wk49.zip','pgb20011211_wk50.zip','pgb20011218_wk51.zip','pgb20011225_wk52.zip ']
filenames[2002] = [
    'pgb20020101_wk01.zip','pgb20020108_wk02.zip','pgb20020115_wk03.zip','pgb20020122_wk04.zip',
    'pgb20020129_wk05.zip','pgb20020205_wk06.zip','pgb20020212_wk07.zip','pgb20020219_wk08.zip',
    'pgb20020226_wk09.zip','pgb20020305_wk10.zip','pgb20020312_wk11.zip','pgb20020319_wk12.zip',
    'pgb20020326_wk13.zip','pgb20020402_wk14.zip','pgb20020409_wk15.zip','pgb20020416_wk16.zip',
    'pgb20020423_wk17.zip','pgb20020430_wk18.zip','pgb20020507_wk19.zip','pgb20020514_wk20.zip',
    'pgb20020521_wk21.zip','pgb20020528_wk22.zip','pgb20020604_wk23.zip','pgb20020611_wk24.zip',
    'pgb20020618_wk25.zip','pgb20020625_wk26.zip','pgb20020702_wk27.zip','pgb20020709_wk28.zip',
    'pgb20020716_wk29.zip','pgb20020723_wk30.zip','pgb20020730_wk31.zip','pgb20020806_wk32.zip',
    'pgb20020813_wk33.zip','pgb20020820_wk34.zip','pgb20020827_wk35.zip','pgb20020903_wk36.zip',
    'pgb20020910_wk37.zip','pgb20020917_wk38.zip','pgb20020924_wk39.zip','pgb20021001_wk40.zip',
    'pgb20021008_wk41.zip','pgb20021015_wk42.zip','pgb20021022_wk43.zip','pgb20021029_wk44.zip',
    'pgb20021105_wk45.zip','pgb20021112_wk46.zip','pgb20021119_wk47.zip','pgb20021126_wk48.zip',
    'pgb20021203_wk49.zip','pgb20021210_wk50.zip','pgb20021217_wk51.zip','pgb20021224_wk52.zip',
    'pgb20021231_wk53.zip']
filenames[2003] = [
    'pgb20030107_wk01.zip','pgb20030114_wk02.zip','pgb20030121_wk03.zip','pgb20030128_wk04.zip',
    'pgb20030204_wk05.zip','pgb20030211_wk06.zip','pgb20030218_wk07.zip','pgb20030225_wk08.zip',
    'pgb20030304_wk09.zip','pgb20030311_wk10.zip','pgb20030318_wk11.zip','pgb20030325_wk12.zip',
    'pgb20030401_wk13.zip','pgb20030408_wk14.zip','pgb20030415_wk15.zip','pgb20030422_wk16.zip',
    'pgb20030429_wk17.zip','pgb20030506_wk18.zip','pgb20030513_wk19.zip','pgb20030520_wk20.zip',
    'pgb20030527_wk21.zip','pgb20030603_wk22.zip','pgb20030610_wk23.zip','pgb20030617_wk24.zip',
    'pgb20030624_wk25.zip','pgb20030701_wk26.zip','pgb20030708_wk27.zip','pgb20030715_wk28.zip',
    'pgb20030722_wk29.zip','pgb20030729_wk30.zip','pgb20030805_wk31.zip','pgb20030812_wk32.zip',
    'pgb20030819_wk33.zip','pgb20030826_wk34.zip','pgb20030902_wk35.zip','pgb20030909_wk36.zip',
    'pgb20030916_wk37.zip','pgb20030923_wk38.zip','pgb20030930_wk39.zip','pgb20031007_wk40.zip',
    'pgb20031014_wk41.zip','pgb20031021_wk42.zip','pgb20031028_wk43.zip','pgb20031104_wk44.zip',
    'pgb20031111_wk45.zip','pgb20031118_wk46.zip','pgb20031125_wk47.zip','pgb20031202_wk48.zip',
    'pgb20031209_wk49.zip','pgb20031216_wk50.zip','pgb20031223_wk51.zip','pgb20031230_wk52.zip']
filenames[2004] = [
    'pgb20040106_wk01.zip','pgb20040113_wk02.zip','pgb20040120_wk03.zip','pgb20040127_wk04.zip',
    'pgb20040203_wk05.zip','pgb20040210_wk06.zip','pgb20040217_wk07.zip','pgb20040224_wk08.zip',
    'pgb20040302_wk09.zip','pgb20040309_wk10.zip','pgb20040316_wk11.zip','pgb20040323_wk12.zip',
    'pgb20040330_wk13.zip','pgb20040406_wk14.zip','pgb20040413_wk15.zip','pgb20040420_wk16.zip',
    'pgb20040427_wk17.zip','pgb20040504_wk18.zip','pgb20040511_wk19.zip','pgb20040518_wk20.zip',
    'pgb20040525_wk21.zip','pgb20040601_wk22.zip','pgb20040608_wk23.zip','pgb20040615_wk24.zip',
    'pgb20040622_wk25.zip','pgb20040629_wk26.zip','pgb20040706_wk27.zip','pgb20040713_wk28.zip',
    'pgb20040720_wk29.zip','pgb20040727_wk30.zip','pgb20040803_wk31.zip','pgb20040810_wk32.zip',
    'pgb20040817_wk33.zip','pgb20040824_wk34.zip','pgb20040831_wk35.zip','pgb20040907_wk36.zip',
    'pgb20040914_wk37.zip','pgb20040921_wk38.zip','pgb20040928_wk39.zip','pgb20041005_wk40.zip',
    'pgb20041012_wk41.zip','pgb20041019_wk42.zip','pgb20041026_wk43.zip','pgb20041102_wk44.zip',
    'pgb20041109_wk45.zip','pgb20041116_wk46.zip','pgb20041123_wk47.zip','pgb20041130_wk48.zip',
    'pgb20041207_wk49.zip','pgb20041214_wk50.zip','pgb20041221_wk51.zip','pgb20041228_wk52.zip']
filenames[2005] = [
             'ipgb20050104_wk01.zip','ipgb20050111_wk02.zip','ipgb20050118_wk03.zip','ipgb20050125_wk04.zip',
             'ipgb20050201_wk05.zip','ipgb20050208_wk06.zip','ipgb20050215_wk07.zip','ipgb20050222_wk08.zip',
             'ipgb20050301_wk09.zip','ipgb20050308_wk10.zip','ipgb20050315_wk11.zip','ipgb20050322_wk12.zip',
             'ipgb20050329_wk13.zip','ipgb20050405_wk14.zip','ipgb20050412_wk15.zip','ipgb20050419_wk16.zip',
             'ipgb20050426_wk17.zip','ipgb20050503_wk18.zip','ipgb20050510_wk19.zip','ipgb20050517_wk20.zip',
             'ipgb20050524_wk21.zip','ipgb20050531_wk22.zip','ipgb20050607_wk23.zip','ipgb20050614_wk24.zip',
             'ipgb20050621_wk25.zip','ipgb20050628_wk26.zip','ipgb20050705_wk27.zip','ipgb20050712_wk28.zip',
             'ipgb20050719_wk29.zip','ipgb20050726_wk30.zip','ipgb20050802_wk31.zip','ipgb20050809_wk32.zip',
             'ipgb20050816_wk33.zip','ipgb20050823_wk34.zip','ipgb20050830_wk35.zip','ipgb20050906_wk36.zip',
             'ipgb20050913_wk37.zip','ipgb20050920_wk38.zip','ipgb20050927_wk39.zip','ipgb20051004_wk40.zip',
             'ipgb20051011_wk41.zip','ipgb20051018_wk42.zip','ipgb20051025_wk43.zip','ipgb20051101_wk44.zip',
             'ipgb20051108_wk45.zip','ipgb20051115_wk46.zip','ipgb20051122_wk47.zip','ipgb20051129_wk48.zip',
             'ipgb20051206_wk49.zip','ipgb20051213_wk50.zip','ipgb20051220_wk51.zip','ipgb20051227_wk52.zip']
filenames[2006] = [
             'ipgb20060103_wk01.zip',
             'ipgb20060110_wk02.zip','ipgb20060117_wk03.zip','ipgb20060124_wk04.zip','ipgb20060131_wk05.zip',
             'ipgb20060207_wk06.zip','ipgb20060214_wk07.zip','ipgb20060221_wk08.zip','ipgb20060228_wk09.zip',
             'ipgb20060307_wk10.zip','ipgb20060314_wk11.zip','ipgb20060321_wk12.zip','ipgb20060328_wk13.zip',
             'ipgb20060404_wk14.zip','ipgb20060411_wk15.zip','ipgb20060418_wk16.zip','ipgb20060425_wk17.zip',
             'ipgb20060502_wk18.zip','ipgb20060509_wk19.zip','ipgb20060516_wk20.zip','ipgb20060523_wk21.zip',
             'ipgb20060530_wk22.zip','ipgb20060606_wk23.zip','ipgb20060613_wk24.zip','ipgb20060620_wk25.zip',
             'ipgb20060627_wk26.zip','ipgb20060704_wk27.zip','ipgb20060711_wk28.zip','ipgb20060718_wk29.zip',
             'ipgb20060725_wk30.zip','ipgb20060801_wk31.zip','ipgb20060808_wk32.zip','ipgb20060815_wk33.zip',
             'ipgb20060822_wk34.zip','ipgb20060829_wk35.zip','ipgb20060905_wk36.zip','ipgb20060912_wk37.zip',
             'ipgb20060919_wk38.zip','ipgb20060926_wk39.zip','ipgb20061003_wk40.zip','ipgb20061010_wk41.zip',
             'ipgb20061017_wk42.zip','ipgb20061024_wk43.zip','ipgb20061031_wk44.zip','ipgb20061107_wk45.zip',
             'ipgb20061114_wk46.zip','ipgb20061121_wk47.zip','ipgb20061128_wk48.zip','ipgb20061205_wk49.zip',
             'ipgb20061212_wk50.zip','ipgb20061219_wk51.zip','ipgb20061226_wk52.zip']
filenames[2007] = [
             'ipgb20070102_wk01.zip',
             'ipgb20070109_wk02.zip','ipgb20070116_wk03.zip','ipgb20070123_wk04.zip','ipgb20070130_wk05.zip',
             'ipgb20070206_wk06.zip','ipgb20070213_wk07.zip','ipgb20070220_wk08.zip','ipgb20070227_wk09.zip',
             'ipgb20070306_wk10.zip','ipgb20070313_wk11.zip','ipgb20070320_wk12.zip','ipgb20070327_wk13.zip',
             'ipgb20070403_wk14.zip','ipgb20070410_wk15.zip','ipgb20070417_wk16.zip','ipgb20070424_wk17.zip',
             'ipgb20070501_wk18.zip','ipgb20070508_wk19.zip','ipgb20070515_wk20.zip','ipgb20070522_wk21.zip',
             'ipgb20070529_wk22.zip','ipgb20070605_wk23.zip','ipgb20070612_wk24.zip','ipgb20070619_wk25.zip',
             'ipgb20070626_wk26.zip','ipgb20070703_wk27.zip','ipgb20070710_wk28.zip','ipgb20070717_wk29.zip',
             'ipgb20070724_wk30.zip','ipgb20070731_wk31.zip','ipgb20070807_wk32.zip','ipgb20070814_wk33.zip',
             'ipgb20070821_wk34.zip','ipgb20070828_wk35.zip','ipgb20070904_wk36.zip','ipgb20070911_wk37.zip',
             'ipgb20070918_wk38.zip','ipgb20070925_wk39.zip','ipgb20071002_wk40.zip','ipgb20071009_wk41.zip',
             'ipgb20071016_wk42.zip','ipgb20071023_wk43.zip','ipgb20071030_wk44.zip','ipgb20071106_wk45.zip',
             'ipgb20071113_wk46.zip','ipgb20071120_wk47.zip','ipgb20071127_wk48.zip','ipgb20071204_wk49.zip',
             'ipgb20071211_wk50.zip','ipgb20071218_wk51.zip','ipgb20071225_wk52.zip']
filenames[2008] = [
             'ipgb20080101_wk01.zip','ipgb20080108_wk02.zip',
             'ipgb20080115_wk03.zip','ipgb20080122_wk04.zip','ipgb20080129_wk05.zip','ipgb20080205_wk06.zip',
             'ipgb20080212_wk07.zip','ipgb20080219_wk08.zip','ipgb20080226_wk09.zip','ipgb20080304_wk10.zip',
             'ipgb20080311_wk11.zip','ipgb20080318_wk12.zip','ipgb20080325_wk13.zip','ipgb20080401_wk14.zip',
             'ipgb20080408_wk15.zip','ipgb20080415_wk16.zip','ipgb20080422_wk17.zip','ipgb20080429_wk18.zip',
             'ipgb20080506_wk19.zip','ipgb20080513_wk20.zip','ipgb20080520_wk21.zip','ipgb20080527_wk22.zip',
             'ipgb20080603_wk23.zip','ipgb20080610_wk24.zip','ipgb20080617_wk25.zip','ipgb20080624_wk26.zip',
             'ipgb20080701_wk27.zip','ipgb20080708_wk28.zip','ipgb20080715_wk29.zip','ipgb20080722_wk30.zip',
             'ipgb20080729_wk31.zip','ipgb20080805_wk32.zip','ipgb20080812_wk33.zip','ipgb20080819_wk34.zip',
             'ipgb20080826_wk35.zip','ipgb20080902_wk36.zip','ipgb20080909_wk37.zip','ipgb20080916_wk38.zip',
             'ipgb20080923_wk39.zip','ipgb20080930_wk40.zip','ipgb20081007_wk41.zip','ipgb20081014_wk42.zip',
             'ipgb20081021_wk43.zip','ipgb20081028_wk44.zip','ipgb20081104_wk45.zip','ipgb20081111_wk46.zip',
             'ipgb20081118_wk47.zip','ipgb20081125_wk48.zip','ipgb20081202_wk49.zip','ipgb20081209_wk50.zip',
             'ipgb20081216_wk51.zip','ipgb20081223_wk52.zip','ipgb20081230_wk53.zip']
filenames[2009] = [
             'ipgb20090106_wk01.zip','ipgb20090113_wk02.zip',
             'ipgb20090120_wk03.zip','ipgb20090127_wk04.zip','ipgb20090203_wk05.zip','ipgb20090210_wk06.zip',
             'ipgb20090217_wk07.zip','ipgb20090224_wk08.zip','ipgb20090303_wk09.zip','ipgb20090310_wk10.zip',
             'ipgb20090317_wk11.zip','ipgb20090324_wk12.zip','ipgb20090331_wk13.zip','ipgb20090407_wk14.zip',
             'ipgb20090414_wk15.zip','ipgb20090421_wk16.zip','ipgb20090428_wk17.zip','ipgb20090505_wk18.zip',
             'ipgb20090512_wk19.zip','ipgb20090519_wk20.zip','ipgb20090526_wk21.zip','ipgb20090602_wk22.zip',
             'ipgb20090609_wk23.zip','ipgb20090616_wk24.zip','ipgb20090623_wk25.zip','ipgb20090630_wk26.zip',
             'ipgb20090707_wk27.zip','ipgb20090714_wk28.zip','ipgb20090721_wk29.zip','ipgb20090728_wk30.zip',
             'ipgb20090804_wk31.zip','ipgb20090811_wk32.zip','ipgb20090818_wk33.zip','ipgb20090825_wk34.zip',
             'ipgb20090901_wk35.zip','ipgb20090908_wk36.zip','ipgb20090915_wk37.zip','ipgb20090922_wk38.zip',
             'ipgb20090929_wk39.zip','ipgb20091006_wk40.zip','ipgb20091013_wk41.zip','ipgb20091020_wk42.zip',
             'ipgb20091027_wk43.zip','ipgb20091103_wk44.zip','ipgb20091110_wk45.zip','ipgb20091117_wk46.zip',
             'ipgb20091124_wk47.zip','ipgb20091201_wk48.zip','ipgb20091208_wk49.zip','ipgb20091215_wk50.zip',
             'ipgb20091222_wk51.zip','ipgb20091229_wk52.zip']
filenames[2010] = [
             'ipgb20100105_wk01.zip','ipgb20100112_wk02.zip',
             'ipgb20100119_wk03.zip','ipgb20100126_wk04.zip','ipgb20100202_wk05.zip','ipgb20100209_wk06.zip',
             'ipgb20100216_wk07.zip','ipgb20100223_wk08.zip','ipgb20100302_wk09.zip','ipgb20100309_wk10.zip',
             'ipgb20100316_wk11.zip','ipgb20100323_wk12.zip','ipgb20100330_wk13.zip','ipgb20100406_wk14.zip',
             'ipgb20100413_wk15.zip','ipgb20100420_wk16.zip','ipgb20100427_wk17.zip','ipgb20100504_wk18.zip',
             'ipgb20100511_wk19.zip','ipgb20100518_wk20.zip','ipgb20100525_wk21.zip','ipgb20100601_wk22.zip',
             'ipgb20100608_wk23.zip','ipgb20100615_wk24.zip','ipgb20100622_wk25.zip','ipgb20100629_wk26.zip',
             'ipgb20100706_wk27.zip','ipgb20100713_wk28.zip','ipgb20100720_wk29.zip','ipgb20100727_wk30.zip',
             'ipgb20100803_wk31.zip','ipgb20100810_wk32.zip','ipgb20100817_wk33.zip','ipgb20100824_wk34.zip',
             'ipgb20100831_wk35.zip','ipgb20100907_wk36.zip','ipgb20100914_wk37.zip','ipgb20100921_wk38.zip',
             'ipgb20100928_wk39.zip','ipgb20101005_wk40.zip','ipgb20101012_wk41.zip','ipgb20101019_wk42.zip',
             'ipgb20101026_wk43.zip','ipgb20101102_wk44.zip','ipgb20101109_wk45.zip','ipgb20101116_wk46.zip',
             'ipgb20101123_wk47.zip','ipgb20101130_wk48.zip','ipgb20101207_wk49.zip','ipgb20101214_wk50.zip',
             'ipgb20101221_wk51.zip','ipgb20101228_wk52.zip']
filenames[2011] = [
             'ipgb20110104_wk01.zip','ipgb20110111_wk02.zip',
             'ipgb20110118_wk03.zip','ipgb20110125_wk04.zip','ipgb20110201_wk05.zip','ipgb20110208_wk06.zip',
             'ipgb20110215_wk07.zip','ipgb20110222_wk08.zip','ipgb20110301_wk09.zip','ipgb20110308_wk10.zip',
             'ipgb20110315_wk11.zip','ipgb20110322_wk12.zip','ipgb20110329_wk13.zip','ipgb20110405_wk14.zip',
             'ipgb20110412_wk15.zip','ipgb20110419_wk16.zip','ipgb20110426_wk17.zip','ipgb20110503_wk18.zip',
             'ipgb20110510_wk19.zip','ipgb20110517_wk20.zip','ipgb20110524_wk21.zip','ipgb20110531_wk22.zip',
             'ipgb20110607_wk23.zip','ipgb20110614_wk24.zip','ipgb20110621_wk25.zip','ipgb20110628_wk26.zip',
             'ipgb20110705_wk27.zip','ipgb20110712_wk28.zip','ipgb20110719_wk29.zip','ipgb20110726_wk30.zip',
             'ipgb20110802_wk31.zip','ipgb20110809_wk32.zip','ipgb20110816_wk33.zip','ipgb20110823_wk34.zip',
             'ipgb20110830_wk35.zip','ipgb20110906_wk36.zip','ipgb20110913_wk37.zip','ipgb20110920_wk38.zip',
             'ipgb20110927_wk39.zip','ipgb20111004_wk40.zip','ipgb20111011_wk41.zip','ipgb20111018_wk42.zip',
             'ipgb20111025_wk43.zip','ipgb20111101_wk44.zip','ipgb20111108_wk45.zip','ipgb20111115_wk46.zip',
             'ipgb20111122_wk47.zip','ipgb20111129_wk48.zip','ipgb20111206_wk49.zip','ipgb20111213_wk50.zip',
             'ipgb20111220_wk51.zip','ipgb20111227_wk52.zip']
filenames[2012] = [
             'ipgb20120103_wk01.zip','ipgb20120110_wk02.zip',
             'ipgb20120117_wk03.zip','ipgb20120124_wk04.zip','ipgb20120131_wk05.zip','ipgb20120207_wk06.zip',
             'ipgb20120214_wk07.zip','ipgb20120221_wk08.zip','ipgb20120228_wk09.zip','ipgb20120306_wk10.zip',
             'ipgb20120313_wk11.zip','ipgb20120320_wk12.zip','ipgb20120327_wk13.zip','ipgb20120403_wk14.zip',
             'ipgb20120410_wk15.zip','ipgb20120417_wk16.zip','ipgb20120424_wk17.zip','ipgb20120501_wk18.zip',
             'ipgb20120508_wk19.zip','ipgb20120515_wk20.zip','ipgb20120522_wk21.zip','ipgb20120529_wk22.zip',
             'ipgb20120605_wk23.zip','ipgb20120612_wk24.zip','ipgb20120619_wk25.zip','ipgb20120626_wk26.zip',
             'ipgb20120703_wk27.zip','ipgb20120710_wk28.zip','ipgb20120717_wk29.zip','ipgb20120724_wk30.zip',
             'ipgb20120731_wk31.zip','ipgb20120807_wk32.zip','ipgb20120814_wk33.zip','ipgb20120821_wk34.zip',
             'ipgb20120828_wk35.zip','ipgb20120904_wk36.zip','ipgb20120911_wk37.zip','ipgb20120918_wk38.zip',
             'ipgb20120925_wk39.zip','ipgb20121002_wk40.zip','ipgb20121009_wk41.zip','ipgb20121016_wk42.zip',
             'ipgb20121023_wk43.zip','ipgb20121030_wk44.zip','ipgb20121106_wk45.zip','ipgb20121113_wk46.zip',
             'ipgb20121120_wk47.zip','ipgb20121127_wk48.zip','ipgb20121204_wk49.zip','ipgb20121211_wk50.zip',
             'ipgb20121218_wk51.zip','ipgb20121225_wk52.zip']
filenames[2013] = [
             'ipgb20130101_wk01.zip','ipgb20130108_wk02.zip','ipgb20130115_wk03.zip',
             'ipgb20130122_wk04.zip','ipgb20130129_wk05.zip','ipgb20130205_wk06.zip','ipgb20130212_wk07.zip',
             'ipgb20130219_wk08.zip','ipgb20130226_wk09.zip','ipgb20130305_wk10.zip','ipgb20130312_wk11.zip',
             'ipgb20130319_wk12.zip','ipgb20130326_wk13.zip','ipgb20130402_wk14.zip','ipgb20130409_wk15.zip',
             'ipgb20130416_wk16.zip','ipgb20130423_wk17.zip','ipgb20130430_wk18.zip','ipgb20130507_wk19.zip',
             'ipgb20130514_wk20.zip','ipgb20130521_wk21.zip','ipgb20130528_wk22.zip','ipgb20130604_wk23.zip',
             'ipgb20130611_wk24.zip','ipgb20130618_wk25.zip','ipgb20130625_wk26.zip','ipgb20130702_wk27.zip',
             'ipgb20130514_wk20.zip','ipgb20130521_wk21.zip','ipgb20130528_wk22.zip','ipgb20130604_wk23.zip',
             'ipgb20130611_wk24.zip','ipgb20130618_wk25.zip','ipgb20130625_wk26.zip','ipgb20130702_wk27.zip',
             'ipgb20130709_wk28.zip','ipgb20130716_wk29.zip','ipgb20130723_wk30.zip','ipgb20130730_wk31.zip',
             'ipgb20130806_wk32.zip','ipgb20130813_wk33.zip','ipgb20130820_wk34.zip','ipgb20130827_wk35.zip',
             'ipgb20130903_wk36.zip','ipgb20130910_wk37.zip','ipgb20130917_wk38.zip','ipgb20130924_wk39.zip',
             'ipgb20131001_wk40.zip','ipgb20131008_wk41.zip','ipgb20131015_wk42.zip','ipgb20131022_wk43.zip',
             'ipgb20131029_wk44.zip','ipgb20131105_wk45.zip','ipgb20131112_wk46.zip','ipgb20131119_wk47.zip',
             'ipgb20131126_wk48.zip','ipgb20131203_wk49.zip','ipgb20131210_wk50.zip','ipgb20131217_wk51.zip',
             'ipgb20131224_wk52.zip','ipgb20131231_wk53.zip']
filenames[2014] = [
             'ipgb20140107_wk01.zip','ipgb20140114_wk02.zip','ipgb20140121_wk03.zip','ipgb20140128_wk04.zip',
             'ipgb20140204_wk05.zip','ipgb20140211_wk06.zip','ipgb20140218_wk07.zip','ipgb20140225_wk08.zip',
             'ipgb20140304_wk09.zip','ipgb20140311_wk10.zip','ipgb20140318_wk11.zip','ipgb20140325_wk12.zip',
             'ipgb20140401_wk13.zip','ipgb20140408_wk14.zip','ipgb20140415_wk15.zip']
