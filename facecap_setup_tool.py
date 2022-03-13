from pyfbsdk import *
import pyfbsdk_additions
import os

toolname = "facecap setup tool"


class CharacterSetup(object):
    def __init__(self, face_mesh_model):
        self.face_mesh_model = face_mesh_model
        self._facecap_device_path = ""
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.scene = FBSystem().Scene

    def read_config(self):
        import json
        with open(self.config_path) as f:
            return json.loads(f.read())

    def write_config(self, path):
        pass
        # # create config file
        # config = dict()
        # for i in sender_nodes:
        #     src = i
        #     # to lower camel case
        #     split_src = i.split(" ")
        #     dst =[split_src[0]]
        #     for i in split_src[1:]:
        #         dst.append(i.capitalize())
        #     dst = "".join(dst)
        #     config[src] = dst
        # with open(r"Z:\models\diva\config.json", "w") as f:
        #     f.write(json.dumps(config, indent=4, sort_keys=True))

    def find_node_by_name(self, node, name):
        for i in node.Nodes:
            if i.Name == name:
                return i

    def create_device(self, device_name, name):
        device = FBCreateObject("Browsing/Templates/Devices", device_name, name)
        if not device:
            raise Exception("FaceCap OSC Device plugin was not found ")
        self.scene.Devices.append(device)
        return device

    def setup_facecap(self):
        facecap_device = self.create_device("FaceCap OSC Device", self.face_mesh_model.FullName + "_facecap_device")
        facecap_tweak_device = self.create_device("FaceCap Multconcert",
                                                  self.face_mesh_model.FullName + "_facecap_device")

        face_mesh_property_list = self.face_mesh_model.PropertyList

        # create relation constraint
        facecap_relation_constraint = FBConstraintRelation(self.face_mesh_model.FullName + "_facecap_constraint")

        # add facecap device to relation constraint
        facecap_sender = facecap_relation_constraint.SetAsSource(facecap_device)

        # add facecap tweak device to offset animation
        facecap_tweak_sender = facecap_relation_constraint.SetAsSource(facecap_tweak_device)

        # add mesh to relation constraint
        reciever = facecap_relation_constraint.ConstrainObject(self.face_mesh_model)

        # TODO make more nice name for mappings
        mappings = self.read_config()

        tmp = dict()
        for i in mappings:
            channel = face_mesh_property_list.Find(str(mappings[i]), 1)
            if not channel:
                print('cannot find target channel "{}", skipping!!!'.format(mappings[i]))
                continue
            try:
                channel.SetAnimated(1)
            except AttributeError as err:
                print str(err) + " skipping!!!"
                continue
            tmp[i] = mappings[i]
        # update mappings to just existing items
        mappings = tmp

        sender_nodes = {i.Name: i for i in facecap_sender.AnimationNodeOutGet().Nodes}
        reciever_nodes = {i.Name: i for i in reciever.AnimationNodeInGet().Nodes}

        # create and link alltogather
        for i in mappings:
            src_anim = sender_nodes.get(i)
            scale_offset_node = facecap_relation_constraint.CreateFunctionBox("Number", "Scale And Offset (Number)")
            scale_offset_node.Name = "offset_" + src_anim.Name

            scale_offset_node_in = self.find_node_by_name(scale_offset_node.AnimationNodeInGet(), "X")
            scale_offset_node_out = self.find_node_by_name(scale_offset_node.AnimationNodeOutGet(), "Result")

            tgt_anim = reciever_nodes[mappings[i]]

            if not src_anim:
                print('cannot find source channel "{}", skipping!!!'.format(mappings[i]))
                continue

            # connections
            FBConnect(src_anim, scale_offset_node_in)
            FBConnect(scale_offset_node_out, tgt_anim)

        # connect tweak device

def run():
    sel = FBModelList()
    FBGetSelectedModels(sel)
    try:
        model = sel.GetModel(0)
    except Exception as err:
        raise Exception("nothing is selected!!!")
    if sel.count() > 1:
        raise Exception("more than one item was selected!!!")
    elif model.FbxGetObjectSubType() != "FBModel":
        raise Exception("model is not of type mesh")
    char_setup = CharacterSetup(model)
    char_setup.setup_facecap()