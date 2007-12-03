#######################################################
#
# Glidein creation module
# Classes and functions needed to handle dictionary files
#
#######################################################

import os.path
import cgWConsts

########################################
#
# File dictionary classes
#
########################################

class DictFile:
    def __init__(self,dir,fname,sort_keys=False,order_matters=False):
        self.dir=dir
        self.fname=fname
        if sort_keys and order_matters:
            raise RuntimeError,"Cannot preserve the order and sort the keys" 
        self.sort_keys=sort_keys
        self.order_matters=order_matters

        self.is_readonly=False
        
        self.keys=[]
        self.vals={}

    def has_key(self,key):
        return key in self.keys

    def __getitem__(self,key):
        return self.vals[key]

    def get_fname(self):
        return self.fname

    def get_dir(self):
        return self.dir

    def erase(self):
        self.keys=[]
        self.vals={}
        
    def set_readonly(self,readonly=True):
        self.is_readonly=readonly


    def add(self,key,val,allow_overwrite=False):
        if self.is_readonly:
            raise RuntimeError, "Trying to modify a readonly object!"
        
        if key in self.keys:
            if not allow_overwrite:
                raise RuntimeError, "Key '%s' already exists"%key
            elif not self.is_compatible(self.vals[key],val):
                raise RuntimeError, "Key '%s': Value %s not compatible with old value %s"%(key,val,self.vals[key])
        else:
            self.keys.append(key)
        self.vals[key]=val

    def save(self, dir=None, fname=None,sort_keys=None): # if dir and/or fname are not specified, use the defaults specified in __init__
        if dir==None:
            dir=self.dir
        if fname==None:
            fname=self.fname
        if sort_keys==None:
            sort_keys=self.sort_keys


        filepath=os.path.join(dir,fname)
        try:
            fd=open(filepath,"w")
        except IOError,e:
            raise RuntimeError, "Error creating %s: %s"%(filepath,e)
        try:
            header=self.file_header()
            if header!=None:
                fd.write("%s\n"%header)
            if sort_keys:
                keys=self.keys[0:]
                keys.sort()
            else:
                keys=self.keys
            for k in keys:
                fd.write("%s\n"%self.format_val(k))
        finally:
            fd.close()
        return

    def load(self, dir=None, fname=None, change_self=True): # if dir and/or fname are not specified, use the defaults specified in __init__, if they are, and change_self is True, change the self.
        if dir==None:
            dir=self.dir
        if fname==None:
            fname=self.fname

        filepath=os.path.join(dir,fname)
        try:
            fd=open(filepath,"r")
        except IOError,e:
            raise RuntimeError, "Error opening %s: %s"%(filepath,e)
        try:
            lines=fd.readlines()
        finally:
            fd.close()

        idx=0
        for line in lines:
            idx+=1
            if line[-1]=='\n':
                # strip newline
                line=line[:-1]
            try:
                self.parse_val(line)
            except RuntimeError, e:
                raise RuntimeError, "File %s, line %i:%s"%(filepath,idx,str(e))

        if change_self:
            self.dir=dir
            self.fname=fname
        return

    def is_equal(self,other,         # other must be of the same class
                 compare_dir=False,compare_fname=False,
                 compare_keys=None): # if None, use order_matters
        if compare_dir and (self.dir!=other.dir):
            return False
        if compare_fname and (self.fname!=other.fname):
            return False
        if compare_keys==None:
            compare_keys=self.order_matters
        if compare_keys and (self.keys!=other.keys):
            return False
        res=(self.vals==other.vals)
        return res

    # PRIVATE
    def is_compatible(self,old_val,new_val):
        return True # everything is compatible
    
    def file_header(self):
        return None # no header
    
    def format_val(self,key):
        return "%s \t%s"%(key,self.vals[key])

    def parse_val(self,line):
        if line[0]=='#':
            return # ignore comments
        arr=line.split(None,1)
        if len(arr)==0:
            return # empty line
        if len(arr[0])==0:
            return # empty key

        key=arr[0]
        if len(arr)==1:
            val=''
        else:
            val=arr[1]
        return self.add(key,val)

class DictFileTwoKeys(DictFile): # both key and val are keys
    def __init__(self,dir,fname,sort_keys=False,order_matters=False):
        DictFile.__init__(self,dir,fname,sort_keys,order_matters)
        self.keys2=[]
        self.vals2={}

    def has_key2(self,key):
        return key in self.keys2

    def get_val2(self,key):
        return self.vals2[key]

    def erase(self):
        DictFile.erase(self)
        self.keys2=[]
        self.vals2={}

    def add(self,key,val,allow_overwrite=False):
        if self.is_readonly:
            raise RuntimeError, "Trying to modify a readonly object!"
        
        if key in self.keys:
            if not allow_overwrite:
                raise RuntimeError, "Key '%s' already exists"%key
            elif not self.is_compatible(self.vals[key],val):
                raise RuntimeError, "Key '%s': Value %s not compatible with old value %s"%(key,val,self.vals[key])
        else:
            self.keys.append(key)

        if val in self.keys2:
            if not allow_overwrite:
                raise RuntimeError, "Value '%s' already exists"%val
            elif not self.is_compatible2(self.vals2[val],key):
                raise RuntimeError, "Value '%s': Key %s not compatible with old key %s"%(val,key,self.vals2[val])
        else:
            self.keys2.append(val)

        self.vals[key]=val
        self.vals2[val]=key
    
    def is_equal(self,other,         # other must be of the same class
                 compare_dir=False,compare_fname=False,
                 compare_keys=None): # if None, use order_matters
        if compare_dir and (self.dir!=other.dir):
            return False
        if compare_fname and (self.fname!=other.fname):
            return False
        if compare_keys==None:
            compare_keys=self.order_matters
        if compare_keys and ((self.keys!=other.keys) or (self.keys2!=other.keys2)):
            return False
        res=(self.vals==other.vals)
        return res
        
    # PRIVATE
    def is_compatible2(self,old_val2,new_val2):
        return True # everything is compatible


# descriptions
class DescriptionDictFile(DictFileTwoKeys):
    def format_val(self,key):
        return "%s \t%s"%(self.vals[key],key)

    def parse_val(self,line):
        if line[0]=='#':
            return # ignore comments
        arr=line.split(None,1)
        if len(arr)==0:
            return # empty line
        if len(arr)!=2:
            raise RuntimeError,"Not a valid description line: '%s'"%line

        return self.add(arr[1],arr[0])
    
# signatures
class SHA1DictFile(DictFile):
    def format_val(self,key):
        return "%s  %s"%(self.vals[key],key)

    def parse_val(self,line):
        if line[0]=='#':
            return # ignore comments
        arr=line.split(None,1)
        if len(arr)==0:
            return # empty line
        if len(arr)!=2:
            raise RuntimeError,"Not a valid SHA1 line: '%s'"%line

        return self.add(arr[1],arr[0])
    
# summary signatures
# values are (sha1,fname)
class SummarySHA1DictFile(DictFile):
    def add(self,key,val,allow_overwrite=False):
        if not (type(val) in (type(()),type([]))):
            raise RuntimeError, "Values '%s' not a list or tuple"%val
        if len(val)!=2:
            raise RuntimeError, "Values '%s' not (sha1,fname)"%val
        return DictFile.add(self,key,val,allow_overwrite)

    def format_val(self,key):
        return "%s  %s  %s"%(self.vals[key][0],self.vals[key][1],key)

    def parse_val(self,line):
        if line[0]=='#':
            return # ignore comments
        arr=line.split(None,2)
        if len(arr)==0:
            return # empty line
        if len(arr)!=3:
            raise RuntimeError,"Not a valid summary signature line (expected 4, found %i elements): '%s'"%(len(arr),line)

        key=arr[2]
        return self.add(key,(arr[0],arr[1]))

# file_list
class FileDictFile(DictFile):
    def format_val(self,key):
        if self.vals[key]!=None:
            return "%s %s"%(key,self.vals[key])
        else:
            return key

    def parse_val(self,line):
        if line[0]=='#':
            return # ignore comments
        arr=line.split(None,1)
        if len(arr)==0:
            return # empty line
        if len(arr[0])==0:
            return # empty key

        key=arr[0]
        if len(arr)==1:
            val=None
        else:
            val=arr[1]
        return self.add(key,val)

# subsystem
# values are (config_check,wnsubdir,config_out)
class SubsystemDictFile(DictFile):
    def add(self,key,val,allow_overwrite=False):
        if not (type(val) in (type(()),type([]))):
            raise RuntimeError, "Values '%s' not a list or tuple"%val
        if len(val)!=3:
            raise RuntimeError, "Values '%s' not (config_check,wnsubdir,config_out)"%val
        return DictFile.add(self,key,val,allow_overwrite)

    def format_val(self,key):
        return "%s %s %s %s"%(self.vals[key][0],self.vals[key][1],key,self.vals[key][2])# condor_vars

    def parse_val(self,line):
        if line[0]=='#':
            return # ignore comments
        arr=line.split(None,3)
        if len(arr)==0:
            return # empty line
        if len(arr)!=4:
            raise RuntimeError,"Not a valid subsystem line (expected 4, found %i elements): '%s'"%(len(arr),line)

        key=arr[2]
        return self.add(key,(arr[0],arr[1],arr[3]))

# values are (Type,Default,CondorName,Required,Export,UserName)
class VarsDictFile(DictFile):
    def is_compatible(self,old_val,new_val):
        return ((old_val[0]==new_val[0]) and (old_val[4]==new_val[4]))# at least the type and the export must be preserved
    
    def file_header(self):
        return ("# VarName               Type    Default         CondorName                     Req.     Export  UserName           \n"+
                "#                       S=Quote - = No Default  + = VarName                             Condor   - = Do not export \n"+
                "#                                                                                                + = Use VarName   \n"+
                "#                                                                                                @ = Use CondorName\n"
                "###################################################################################################################")

    def add(self,key,val,allow_overwrite=0):
        if not (type(val) in (type(()),type([]))):
            raise RuntimeError, "Values '%s' not a list or tuple"%val
        if len(val)!=6:
            raise RuntimeError, "Values '%s' not (Type,Default,CondorName,Required,Export,UserName)"%val
        if not (val[0] in ('C','S','I')):
            raise RuntimeError,"Invalid var type '%s', should be either C, S or I in val: %s"%(val[1],val)
        for i,t in ((3,"Required"),(4,"Export")):
            if not (val[i] in ('Y','N')):
                raise RuntimeError,"Invalid var %s '%s', should be either Y or N in val: %s"%(t,val[i],val)

        return DictFile.add(self,key,val,allow_overwrite)

    def format_val(self,key):
        return "%s \t%s \t%s \t\t%s \t%s \t%s \t%s"%(key,self.vals[key][0],self.vals[key][1],self.vals[key][2],self.vals[key][3],self.vals[key][4],self.vals[key][5])
        

    def parse_val(self,line):
        if len(line)==0:
            return #ignore emoty lines
        if line[0]=='#':
            return # ignore comments
        arr=line.split(None,6)
        if len(arr)==0:
            return # empty line
        if len(arr)!=7:
            raise RuntimeError,"Not a valid var line (expected 7, found %i elements): '%s'"%(len(arr),line)

        key=arr[0]
        return self.add(key,arr[1:])


################################################
#
# Functions that create default dictionaries
#
################################################

# internal, do not use from outside the module
def get_common_dicts(submit_dir,stage_dir):
    common_dicts={'attrs':DictFile(stage_dir,cgWConsts.ATTRS_FILE),
                  'description':DescriptionDictFile(stage_dir,cgWConsts.DESCRIPTION_FILE),
                  'consts':DictFile(stage_dir,cgWConsts.CONSTS_FILE),
                  'params':DictFile(submit_dir,cgWConsts.PARAMS_FILE),
                  'vars':VarsDictFile(stage_dir,cgWConsts.VARS_FILE),
                  'file_list':FileDictFile(stage_dir,cgWConsts.FILE_LISTFILE),
                  'script_list':FileDictFile(stage_dir,cgWConsts.SCRIPT_LISTFILE),
                  'subsystem_list':SubsystemDictFile(stage_dir,cgWConsts.SUBSYSTEM_LISTFILE),
                  "signature":SHA1DictFile(stage_dir,cgWConsts.SIGNATURE_FILE)}
    refresh_description(common_dicts)
    return common_dicts

def get_main_dicts(submit_dir,stage_dir):
    main_dicts=get_common_dicts(submit_dir,stage_dir)
    main_dicts['summary_signature']=SummarySHA1DictFile(submit_dir,cgWConsts.SUMMARY_SIGNATURE_FILE)
    return main_dicts

def get_entry_dicts(submit_dir,stage_dir,entry_name):
    entry_submit_dir=cgWConsts.get_entry_submit_dir(submit_dir,entry_name)
    entry_stage_dir=cgWConsts.get_entry_stage_dir(stage_dir,entry_name)
    entry_dicts=get_common_dicts(entry_submit_dir,entry_stage_dir)
    return entry_dicts

################################################
#
# Functions that load dictionaries
#
################################################

# internal, do not use from outside the module
def load_common_dicts(dicts,           # update in place
                      description_el):
    # first submit dir ones (mutable)
    dicts['params'].load()
    # all others are keyed in the description
    dicts['signature'].load(fname=description_el.vals2['signature'])
    dicts['attrs'].load(fname=description_el.vals2['attrs_file'])
    dicts['consts'].load(fname=description_el.vals2['consts_file'])
    dicts['vars'].load(fname=description_el.vals2['condor_vars'])
    dicts['file_list'].load(fname=description_el.vals2['file_list'])
    dicts['script_list'].load(fname=description_el.vals2['script_list'])
    dicts['subsystem_list'].load(fname=description_el.vals2['subsystem_list'])

def load_main_dicts(main_dicts): # update in place
    # summary_signature has keys for description
    main_dicts['summary_signature'].load()
    # load the description (need to erase first, as it is always non-empty)
    main_dicts['description'].erase()
    main_dicts['description'].load(fname=main_dicts['summary_signature']['main'][1])
    # all others are keyed in the description
    load_common_dicts(main_dicts,main_dicts['description'])

def load_entry_dicts(entry_dicts,                   # update in place
                     entry_name,summary_signature): 
    # load the description (name from summary_signature, need to erase it first, as it is always non-empty)
    entry_dicts['description'].erase()
    entry_dicts['description'].load(fname=summary_signature[cgWConsts.get_entry_stage_dir("",entry_name)][1])
    # all others are keyed in the description
    load_common_dicts(entry_dicts,entry_dicts['description'])

############################################################
#
# Functions that create data out of the existing dictionary
#
############################################################

def refresh_description(dicts): # update in place
    description_dict=entry_dicts['description']
    description_dict.add(dicts['signature'].get_fname(),"signature",allow_overwrite=True)
    description_dict.add(dicts['attrs'].get_fname(),"attrs_file",allow_overwrite=True)
    description_dict.add(dicts['consts'].get_fname(),"consts_file",allow_overwrite=True)
    description_dict.add(dicts['vars'].get_fname(),"condor_vars",allow_overwrite=True)
    description_dict.add(dicts['file_list'].get_fname(),"file_list",allow_overwrite=True)
    description_dict.add(dicts['script_list'].get_fname(),"script_list",allow_overwrite=True)
    description_dict.add(dicts['subsystem_list'].get_fname(),"subsystem_list",allow_overwrite=True)

################################################
#
# Handle dicts as Classes
#
################################################

# internal, do not use directly from outside the module
class glideinDicts:
    def __init__(self):
        self.dicts=None
        raise RuntimeError, "glideinDicts should never be directly used"
        
    def keys(self):
        return self.dicts.keys()

    def has_key(self,key):
        return self.dicts.has_key(key)

    def __getitem__(self,key):
        return self.dicts[key]        

    def set_readonly(self,readonly=True):
        for el in self.dicts.values():
            el.set_readonly(readonly)


class glideinMainDicts(glideinDicts):
    def __init__(self,submit_dir,stage_dir):
        self.submit_dir=submit_dir
        self.stage_dir=stage_dir
        self.dicts=get_main_dicts(submit_dir,stage_dir)

    def get_summary_signature(self): # you can discover most of the other things from this
        return self.dicts['summary_signature']

    def erase(self):
        self.dicts=get_main_dicts(self.submit_dir,self.stage_dir)
    
    def load(self):
        load_main_dicts(self.dicts)

    def save(self):
        pass # to be defined

    def is_equal(self,other,             # other must be of the same class
                 compare_submit_dir=False,compare_stage_dir=False,
                 compare_fnames=False): 
        if compare_submit_dir and (self.submit_dir!=other.submit_dir):
            return False
        if compare_stage_dir and (self.stage_dir!=other.stage_dir):
            return False
        for k in self.dicts.keys():
            if not self.dicts[k].is_equal(other.dicts[k],compare_dir=False,compare_fname=compare_fnames):
                return False
        return True
        
class glideinEntryDicts(glideinDicts):
    def __init__(self,
                 glidein_main_dicts, # must be an instance of glideinMainDicts
                 entry_name):
        self.entry_name=entry_name
        self.glidein_main_dicts=glidein_main_dicts
        self.submit_dir=glidein_main_dicts.submit_dir
        self.stage_dir=glidein_main_dicts.stage_dir
        self.dicts=get_entry_dicts(self.submit_dir,self.stage_dir,entry_name)

    def erase(self):
        self.dicts=get_entry_dicts(self.submit_dir,self.stage_dir,self.entry_name)
    
    def load(self): #will use glidein_main_dicts data, so it must be loaded first
        load_entry_dicts(self.dicts,self.entry_name,self.glidein_main_dicts.get_summary_signature())

    def save(self):
        pass # to be defined

    def is_equal(self,other,             # other must be of the same class
                 compare_entry_name=False,
                 compare_glidein_main_dicts=False, # if set to True, will do a complete check on the related objects
                 compare_fnames=False): 
        if compare_entry_name and (self.entry_name!=other.entry_name):
            return False
        if compare_glidein_main_dicts and (self.glidein_main_dicts.is_equal(other.glidein_main_dicts,compare_submit_dir=True,compare_stage_dir=True,compare_fnames=compare_fnames)):
            return False
        for k in self.dicts.keys():
            if not self.dicts[k].is_equal(other.dicts[k],compare_dir=False,compare_fname=compare_fnames):
                return False
        return True

################################################
#
# This Class contains coth the main and
# the entry dicts
#
################################################

class glideinDicts:
    def __init__(self,submit_dir,stage_dir,entry_list=[]):
        self.submit_dir=submit_dir
        self.stage_dir=stage_dir
        self.main_dicts=glideinMainDicts(self.submit_dir,self.stage_dir)
        self.entry_dicts={}
        for entry_name in entry_list:
            self.entry_dicts[entry_name]=glideinEntryDicts(self.main_dicts,entry_name)
        return

    def set_readonly(self,readonly=True):
        self.main_dicts.set_readonly(readonly)
        for el in self.entry_dicts.values():
            el.set_readonly(readonly)

    def erase(self,destroy_old_entries=True): # if false, the entry names will be preserved
        self.main_dicts=glideinMainDicts(self.submit_dir,self.stage_dir)
        if destroy_old_entries:
            self.entry_dicts={}
        else:
            for entry_name in self.entry_dicts.keys():
                self.entry_dicts[entry_name]=glideinEntryDicts(self.main_dicts,entry_name)
        return

    def load(self,destroy_old_entries=True): # if false, overwrite the entries you load, but leave the others as they are
        self.main_dicts.load()
        if destroy_old_entries:
            self.entry_dicts={}
        # else just leave as it is, will rewrite just the loaded ones

        for sign_key in self.main_dicts.get_summary_signature().keys:
            if sign_key!='main': # main is special, not an entry
                entry_name=cgWConsts.get_entry_name_from_entry_stage_dir(sign_key)
                self.entry_dicts[entry_name]=glideinEntryDicts(self.main_dicts,entry_name)
                self.entry_dicts[entry_name].load()

    def save(self):
        pass # to be defined
   
    def is_equal(self,other,             # other must be of the same class
                 compare_submit_dir=False,compare_stage_dir=False,
                 compare_fnames=False): 
        if compare_submit_dir and (self.submit_dir!=other.submit_dir):
            return False
        if compare_stage_dir and (self.stage_dir!=other.stage_dir):
            return False
        if not self.main_dicts.is_equal(other.main_dicts,compare_submit_dir=False,compare_stage_dir=False,compare_fnames=compare_fnames):
            return False
        my_entries=self.entry_dicts.keys()
        other_entries=other.entry_dicts.keys()
        if len(my_entries)!=len(other_entries):
            return False

        my_entries.sort()
        other_entries.sort()
        if my_entries!=other_entries: # need to be in the same order to make a comparison
            return False
        
        for k in my_entries:
            if not self.entry_dicts[k].is_equal(other.entry_dicts[k],compare_entry_name=False,
                                                compare_glidein_main_dicts=False,compare_fname=compare_fnames):
                return False
        return True

###########################################################
#
# CVS info
#
# $Id: cgWDictFile.py,v 1.14 2007/12/03 20:15:00 sfiligoi Exp $
#
# Log:
#  $Log: cgWDictFile.py,v $
#  Revision 1.14  2007/12/03 20:15:00  sfiligoi
#  Change create_description in refresh_description and use it
#
#  Revision 1.13  2007/12/03 19:49:20  sfiligoi
#  Added create_description, plus a little bit of cleanup
#
#  Revision 1.12  2007/12/03 19:23:56  sfiligoi
#  Get rid of duplicates
#
#  Revision 1.11  2007/11/30 22:49:06  sfiligoi
#  Make changing of self optional in load
#
#  Revision 1.10  2007/11/28 22:22:49  sfiligoi
#  Fix typo
#
#  Revision 1.9  2007/11/28 22:20:58  sfiligoi
#  Add is_equal to all classes
#
#  Revision 1.8  2007/11/28 21:27:06  sfiligoi
#  Add keys function to glideinMainDicts and glideinEntryDicts
#
#  Revision 1.6  2007/11/28 21:13:27  sfiligoi
#  Add glideinDicts (also fixed load_entry_dicts)
#
#  Revision 1.4  2007/11/28 19:54:50  sfiligoi
#  Add load_entry_dicts
#
#  Revision 1.3  2007/11/28 19:45:19  sfiligoi
#  Add load_main_dicts
#
#  Revision 1.2  2007/11/27 19:58:51  sfiligoi
#  Move dicts initialization into cgWDictFile and entry subdir definition in cgWConsts
#
#  Revision 1.1  2007/10/25 22:28:27  sfiligoi
#  FIle dictionary classes
#
#
###########################################################
