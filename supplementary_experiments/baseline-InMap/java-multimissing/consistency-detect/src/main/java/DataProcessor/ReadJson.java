package DataProcessor;

import Model.Dependency.CellsDTO;
import Model.Dependency.DependencyData;
import Model.Dependency.DetailsDTO;
import Model.Dependency.IndicesDTO;
import Model.JsonUtil;
import Model.Reflexion.ReflectionModel;
import Model.Reflexion.StructureDTO;
import Model.Target.TargetModel;

import java.io.*;
import java.util.*;

public class ReadJson {

    public List<String> moduleList=new ArrayList<>();
    public HashMap<String, String> entity_file = new HashMap<>();
    public HashMap<Integer, String> num_entity = new HashMap<>();
    public HashMap<String, Integer> entity_line = new HashMap<>();
    public HashMap<String, Integer> entity_row = new HashMap<>();
    public HashMap<String, String> entity_type = new HashMap<>();
    public List<String> field_classVar = new ArrayList<>();
    public List<String> field_instanceVar = new ArrayList<>();
    public List<String> func_individual = new ArrayList<>();
    public List<String> func_individual_public = new ArrayList<>();
    public List<String> func_notOverride = new ArrayList<>();
    public List<String> field_type = new ArrayList<>();
    public List<String> func_type = new ArrayList<>();
    public HashMap<String, List<String>> method_parameter_target = new HashMap<>();
    public HashMap<String, List<String>> field_refenced_target = new HashMap<>();
    public HashMap<String, List<String>> create_dep = new HashMap<>();
    public HashMap<String, List<String>> extend_dep = new HashMap<>();
    public HashMap<String, List<String>> return_dep = new HashMap<>();
    public HashMap<String, List<String>> module_file = new HashMap<>();
    //public static List<String> reflexion_file_list =new ArrayList<>(); //the related items have all been commented out
    public HashMap<String, List<String>> dependencies = new HashMap<>();
    public HashMap<String, List<String>> dependencies_reverse = new HashMap<>();
    public HashMap<String, List<String>> target_model_dependencies = new HashMap<>();
    public HashMap<String, List<String>> class_func = new HashMap<>();
    public HashMap<String, List<String>> class_allMethod = new HashMap<>();
    public HashMap<String, List<String>> class_allVar = new HashMap<>();
    public HashMap<String, List<String>> class_field = new HashMap<>();
    public HashMap<String, List<String>> method_localVar = new HashMap<>();
    public HashMap<String, List<String>> super_subs_class = new HashMap<>();
    public HashMap<String, String> sub_super_class = new HashMap<>();
    public List<String> innerClassList=new ArrayList<>();
    public HashMap<String, List<String>> sub_supers_class_implement = new HashMap<>();
    public List<String> staticMethod = new ArrayList<>();
    public List<String> abstractClass = new ArrayList<>();

    public ReadJson() {

    }

    public void getMethodFieldInClass(String dep_json) {
        //String jsonPath = "E:\\Refactoring\\OptJava-master\\HW10 - NSGA2\\src\\main\\java\\hr\\fer\\zemris\\optjava\\dz10\\nsga\\refactoring\\input\\depends.dep.json";
        DependencyData dependencyData = JsonUtil.getGSONObject1(new File(dep_json));
        assert dependencyData != null;
        List<IndicesDTO> indicesArray = dependencyData.getIndices();
        List<String> Class_type = new ArrayList<>();
        HashMap<String, List<String>> File_class = new HashMap<>();
        HashMap<String, List<String>> class_func1 = new HashMap<>();
        HashMap<String, List<String>> class_field1 = new HashMap<>();
        HashMap<String, String> field_rawtype = new HashMap<>();
        List<String> field_localVar = new ArrayList<>();
        List<String> AllMethod = new ArrayList<>();
        List<String> AllVar = new ArrayList<>();

        //HashMap<String,String> class = new HashMap<>();
        int i = 0;
        for (IndicesDTO indicesDTO : indicesArray) {
            String file=indicesDTO.getFile();
//            file=file.substring(file.indexOf("org/apache")); //only Hadoopadd this line; do not add it for other projects
            entity_file.put(indicesDTO.getObject(), file);
            num_entity.put(i, indicesDTO.getObject());
            entity_type.put(indicesDTO.getObject(), indicesDTO.getType());
            entity_line.put(indicesDTO.getObject(), indicesDTO.getLocation().getLine());
            entity_row.put(indicesDTO.getObject(), indicesDTO.getLocation().getRow());
            String type = indicesDTO.getType();
            String local = indicesDTO.getExtendVarType();
            Boolean isOverride = indicesDTO.getIsOverride();
            Boolean isSetter = indicesDTO.getIsSetter();
            Boolean isGetter = indicesDTO.getIsGetter();
            Boolean isAssign = indicesDTO.getIsAssign();
            Boolean isConstructor = indicesDTO.getIsConstructor();
            Boolean isPublic = indicesDTO.getIsPublic();
            Boolean isCallSuper = indicesDTO.getIsCallSuper();
            Boolean isAbstract = indicesDTO.getMethodIsAbstract();
            Boolean isStatic = indicesDTO.getIsStatic();
            Boolean typeIsAbstract=indicesDTO.getTypeIsAbstract();



            if (type.equals("Type")) {
                Class_type.add(indicesDTO.getObject());
                String File = indicesDTO.getFile();
                String Object = indicesDTO.getObject();
                List<String> list;
                if (File_class.containsKey(File)) {
                    list = File_class.get(File);
                } else {
                    list = new ArrayList<>();
                }//Assume there is only one class in a file
                list.add(Object);
                File_class.put(File, list);
                if ((typeIsAbstract!=null)&&(typeIsAbstract)){
                    abstractClass.add(indicesDTO.getObject());
                }
            }
            if (type.equals("FuncImpl")) {
                AllMethod.add(indicesDTO.getObject());
                func_type.add(indicesDTO.getObject());
                if (((isOverride != null) && (!isOverride)) && ((isSetter != null) && (!isSetter)) && ((isGetter != null) && (!isGetter)) && ((isAssign != null) && (!isAssign)) && ((isConstructor != null) && (!isConstructor)) && ((isCallSuper != null) && (!isCallSuper)) && ((isAbstract != null) && (!isAbstract))) {  //&&isConstructor!=null)&&(!isConstructor)
                    func_individual.add(indicesDTO.getObject());
                }

                if (((isOverride != null) && (!isOverride)) && ((isConstructor != null) && (!isConstructor)) && ((isPublic != null) && (isPublic))) {  //
                    func_individual_public.add(indicesDTO.getObject());
                }
                if (((isOverride != null) && (!isOverride))&& ((isConstructor != null) && (!isConstructor))&&((isSetter != null) && (!isSetter)) && ((isGetter != null) && (!isGetter)) && ((isAssign != null) && (!isAssign))) {
                    func_notOverride.add(indicesDTO.getObject());
                }
                if (((isStatic != null) && (isStatic)) && ((isConstructor != null) && (!isConstructor))){
                    staticMethod.add(indicesDTO.getObject());
                }
            }

            if (type.equals("Var")) {
                AllVar.add(indicesDTO.getObject());
                if ((local != null) && (!local.equals("LocalVar"))) {
                    field_type.add(indicesDTO.getObject());
                }
                if ((local != null) && (local.equals("ClassVar"))) {
                    field_classVar.add(indicesDTO.getObject());
                }
                if ((local != null) && (local.equals("InstanceVar"))) {
                    field_instanceVar.add(indicesDTO.getObject());
                }
                if ((local != null) && (local.equals("LocalVar"))) {
                    field_localVar.add(indicesDTO.getObject());
                }
                field_rawtype.put(indicesDTO.getObject(), indicesDTO.getRawType());

            }

            i = i + 1;
        }


        for (String class_type : Class_type) {
            for (String func_type : func_type) {
                if (func_type.substring(0, func_type.lastIndexOf('.')).equals(class_type)) {
                    List<String> list;
                    if (class_func.containsKey(class_type)) {
                        list = class_func.get(class_type);
                    } else {
                        list = new ArrayList<>();
                    }
                    if (!list.contains(func_type)){
                        list.add(func_type);
                    }
                    class_func.put(class_type, list);
                }
            }
            for (String field_type : field_type) {
                if (field_type.substring(0, field_type.lastIndexOf('.')).equals(class_type)) {
                    List<String> list;
                    if (class_field.containsKey(class_type)) {
                        list = class_field.get(class_type);
                    } else {
                        list = new ArrayList<>();
                    }
                    list.add(field_type);
                    class_field.put(class_type, list);
                }
            }
            for (String func_type : func_individual) {
                if (func_type.contains(class_type)) {
                    List<String> list;
                    if (class_func1.containsKey(class_type)) {
                        list = class_func1.get(class_type);
                    } else {
                        list = new ArrayList<>();
                    }
                    list.add(func_type);
                    class_func1.put(class_type, list);
                }
            }
            for (String field_type : field_classVar) {
                if (field_type.contains(class_type)) {
                    List<String> list;
                    if (class_field1.containsKey(class_type)) {
                        list = class_field1.get(class_type);
                    } else {
                        list = new ArrayList<>();
                    }
                    list.add(field_type);
                    class_field1.put(class_type, list);
                }
            }
            for (String method : AllMethod) {
                if (method.contains(class_type)) {
                    List<String> list;
                    if (class_allMethod.containsKey(class_type)) {
                        list = class_allMethod.get(class_type);
                    } else {
                        list = new ArrayList<>();
                    }
                    list.add(method);
                    class_allMethod.put(class_type, list);
                }
            }
            for (String var : AllVar) {
                if (var.contains(class_type)) {
                    List<String> list;
                    if (class_allVar.containsKey(class_type)) {
                        list = class_allVar.get(class_type);
                    } else {
                        list = new ArrayList<>();
                    }
                    list.add(var);
                    class_allVar.put(class_type, list);
                }
            }

            for (String class_type1 : Class_type) {
                if (class_type1.contains(".")){
                    if (class_type1.substring(0, class_type1.lastIndexOf('.')).equals(class_type)) {
                        innerClassList.add(class_type1);
                    }
                }

            }
        }


        for (String field : field_rawtype.keySet()) {
            String fieldinclass = null;
            String target = null;
            if (!field_type.contains(field)) {
                continue;
            }
            String raw = field_rawtype.get(field);
            for (String class_type : Class_type) {
                String classType = class_type.substring(class_type.lastIndexOf(".") + 1);
                if (classType.equals(raw)) {
                    target = class_type;
                }
            }
            if (target == null) {
                continue;
            }
            for (String class_type : Class_type) {
                //List<String> class_type1= Arrays.asList(class_type.split(","));
                if (field.contains(class_type)) {
                    fieldinclass = class_type;
                }
            }

            if (field_refenced_target.containsKey(fieldinclass)) {
                List<String> list = field_refenced_target.get(fieldinclass);

                list.add(target);
                field_refenced_target.put(fieldinclass, list);

            } else {
                List<String> list = new ArrayList<>();
                list.add(target);
                field_refenced_target.put(fieldinclass, list);
            }
        }

        for (String func_type : AllMethod) {
            for (String localVar : AllVar) {  //Find this method's local variables from all variables
                if (localVar.contains(func_type)) {
                    List<String> list;
                    if ((method_localVar.containsKey(func_type)) && (!localVar.equals(func_type))) {
                        list = method_localVar.get(func_type);
                    } else {
                        list = new ArrayList<>();
                    }
                    list.add(localVar);
                    method_localVar.put(func_type, list);
                }
            }
        }


    }

    public void resolveExtendRelation(String dep_json) {
        //String jsonPath = "E:\\Refactoring\\OptJava-master\\HW10 - NSGA2\\src\\main\\java\\hr\\fer\\zemris\\optjava\\dz10\\nsga\\refactoring\\input\\depends.dep.json";
        DependencyData dependencyData = JsonUtil.getGSONObject1(new File(dep_json));
        List<CellsDTO> cellsArray = dependencyData.getCells();
        for (CellsDTO cellsDTO : cellsArray) {
            List<DetailsDTO> detailsArray = cellsDTO.getDetails();
            for (DetailsDTO detailsDTO : detailsArray) {
                int from = detailsDTO.getFrom();
                int to = detailsDTO.getTo();
                String type = detailsDTO.getType();
                if (type.equals("Extend")) {
                    String from_entity = num_entity.get(from);
                    String to_entity = num_entity.get(to);
                    List<String> list;
                    if (super_subs_class.containsKey(to_entity)) {
                        list = super_subs_class.get(to_entity);
                    } else {
                        list = new ArrayList<>();
                    }
                    list.add(from_entity);
                    super_subs_class.put(to_entity, list);
                    sub_super_class.put(from_entity, to_entity);
                }

            }
        }
    }

    public void resolveImplementRelation(String dep_json) {
        DependencyData dependencyData = JsonUtil.getGSONObject1(new File(dep_json));
        HashMap<String, List<String>> implementList = new HashMap<>();
        List<CellsDTO> cellsDTOList = dependencyData.getCells();
        for (CellsDTO cellsDTO : cellsDTOList) {
            if (!cellsDTO.getSrc().equals(cellsDTO.getDest())) {
                if (cellsDTO.getValues().getImplement() != null) {
                    List<DetailsDTO> detailsDTOList = cellsDTO.getDetails();
                    for (DetailsDTO detailsDTO : detailsDTOList) {
                        if (detailsDTO.getType().equals("Implement")) {
                            int from = detailsDTO.getFrom();
                            int to = detailsDTO.getTo();
                            String from_entity = num_entity.get(from);
                            String to_entity = num_entity.get(to);

                            implementList.computeIfAbsent(from_entity, k -> new ArrayList<>());
                            implementList.get(from_entity).add(to_entity);
                        }
                    }
                }
            }
        }
        this.sub_supers_class_implement = implementList;
    }


    public void Dependencies(String dep_json) {
        //String jsonPath = "E:\\Refactoring\\OptJava-master\\HW10 - NSGA2\\src\\main\\java\\hr\\fer\\zemris\\optjava\\dz10\\nsga\\refactoring\\input\\depends.dep.json";
        DependencyData dependencyData = JsonUtil.getGSONObject1(new File(dep_json));
        List<CellsDTO> cellsArray = dependencyData.getCells();

        for (CellsDTO cellsDTO : cellsArray) {
            List<DetailsDTO> detailsArray = cellsDTO.getDetails();
            for (DetailsDTO detailsDTO : detailsArray) {
                int from = detailsDTO.getFrom();
                int to = detailsDTO.getTo();



                String from_type = entity_type.get(num_entity.get(from));
                String to_type = entity_type.get(num_entity.get(to));

                if (!from_type.equals("File")) {

                    String type = detailsDTO.getType();
                    String from_entity = num_entity.get(from);
                    String to_entity = num_entity.get(to);
                    if (from_entity.equals("depends.entity.FileEntity")){
                        int f=1;
                    }
                    if (type.equals("Create")){// || (to_entity.equals("depends.entity.AliasEntity.deepResolve"))) {
                        if (create_dep.containsKey(from_entity)) {
                            List<String> list = create_dep.get(from_entity);
                            if (!list.contains(to_entity)) {
                                list.add(to_entity);
                                create_dep.put(from_entity, list);
                            }
                        } else {
                            List<String> list = new ArrayList<>();
                            list.add(to_entity);
                            create_dep.put(from_entity, list);
                        }
                    }
                    if ((from_type.equals("FuncImpl")) && (to_type.equals("Type")) && (type.equals("Parameter"))) {
                        if (method_parameter_target.containsKey(from_entity)) {
                            List<String> list = method_parameter_target.get(from_entity);
                            if (!list.contains(to_entity)) {
                                list.add(to_entity);
                                method_parameter_target.put(from_entity, list);
                            }
                        } else {
                            List<String> list = new ArrayList<>();
                            list.add(to_entity);
                            method_parameter_target.put(from_entity, list);
                        }

                    }
                    if ((from_type.equals("FuncImpl")) && (to_type.equals("Type")) && (type.equals("Return"))) {
                        if (return_dep.containsKey(from_entity)) {
                            List<String> list = return_dep.get(from_entity);
                            if (!list.contains(to_entity)) {
                                list.add(to_entity);
                                return_dep.put(from_entity, list);
                            }
                        } else {
                            List<String> list = new ArrayList<>();
                            list.add(to_entity);
                            return_dep.put(from_entity, list);
                        }

                    }
                    if ((type.equals("Extend"))) {
                        if (extend_dep.containsKey(from_entity)) {
                            List<String> list = extend_dep.get(from_entity);
                            if (!list.contains(to_entity)) {
                                list.add(to_entity);
                                extend_dep.put(from_entity, list);
                            }
                        } else {
                            List<String> list = new ArrayList<>();
                            list.add(to_entity);
                            extend_dep.put(from_entity, list);
                        }

                    }
                    //int line = detailsDTO.getLine();
                    if (dependencies.containsKey(from_entity)) {
                        List<String> list = dependencies.get(from_entity);
                        if (!list.contains(to_entity)) {
                            list.add(to_entity);
                            dependencies.put(from_entity, list);
                        }
                    } else {
                        List<String> list = new ArrayList<>();
                        list.add(to_entity);
                        dependencies.put(from_entity, list);
                    }
                    if (dependencies_reverse.containsKey(to_entity)) {
                        List<String> list = dependencies_reverse.get(to_entity);
                        if (!list.contains(from_entity)) {
                            list.add(from_entity);
                            dependencies_reverse.put(to_entity, list);
                        }
                    } else {
                        List<String> list = new ArrayList<>();
                        list.add(from_entity);
                        dependencies_reverse.put(to_entity, list);
                    }
                }
            }
        }

    }

    public void resolvePackageFiles(String rfx_json) {
        ReflectionModel reflectionModel = JsonUtil.getGSONObject2(new File(rfx_json));
        List<StructureDTO> structureArray = reflectionModel.getStructure();

        for (StructureDTO structureDTO : structureArray) {
            String name = structureDTO.getName();
            List<StructureDTO> nested = structureDTO.getNested();
            HashMap<String, List<String>> module_file = new HashMap<>();
            List<String> file = new ArrayList<>();
            HashMap<String, List<String>> sub_module_file = new HashMap<>();
            for (StructureDTO structureDTO1 : nested) {
                String name1 = structureDTO1.getName();
                List<StructureDTO> nested1 = structureDTO1.getNested();
                if (nested1 != null) {
                    sub_module_file = recursion(name1, nested1);
                    moduleList.add(name1);

                } else {
                    //rawnameNew
                    name1 = structureDTO1.getRawName();
                    //
                    file.add(name1);
                    module_file.put(name, file);
//                    if (!reflexion_file_list.contains(name1)){
//                        reflexion_file_list.add(name1);
//                    }
                }
                this.module_file.putAll(module_file);
                this.module_file.putAll(sub_module_file);
            }

        }

        /* Hadoop-specific code!
        HashMap<String, List<String>> file_Module = new HashMap<String, List<String>>();
        for (String module : module_file.keySet()) {
            for (String file : module_file.get(module)) {
                if (!file_Module.containsKey(file)) {
                    List<String> list = new ArrayList<String>();
                    list.add(module);
                    file_Module.put(file, list);
                } else {
                    List<String> list = file_Module.get(file);
                    list.add(module);
                    file_Module.put(file, list);

                }
            }
        }
        for (String file:file_Module.keySet()){
            List<String>moduleList=file_Module.get(file);
            for (String module:moduleList){
                if (module.contains("org")){
                    List<String>list=new ArrayList<>();
                    list.add(module);
                    file_Module.put(file,list);
                    break;
                }
            }
        }
        module_file=new HashMap<>();
        for (String module : file_Module.keySet()) {
            for (String file : file_Module.get(module)) {
                if (!module_file.containsKey(file)) {
                    List<String> list = new ArrayList<String>();
                    list.add(module);
                    module_file.put(file, list);
                } else {
                    List<String> list = module_file.get(file);
                    list.add(module);
                    module_file.put(file, list);

                }
            }
        }

        */


    }

    public HashMap<String, List<String>> recursion(String name, List<StructureDTO> nested) {
        HashMap<String, List<String>> module_file = new HashMap<>();
        List<String> file = new ArrayList<>();
        HashMap<String, List<String>> combineResultMap = new HashMap<>();
        HashMap<String, List<String>> sub_module_file = new HashMap<>();
        for (StructureDTO structureDTO1 : nested) {
            String name1 = structureDTO1.getName();
            List<StructureDTO> nested1 = structureDTO1.getNested();
            if (nested1 != null) {
                moduleList.add(name);
                sub_module_file = recursion(name1, nested1);
            } else {
                //rawnameNew
                name1 = structureDTO1.getRawName();
                //
                file.add(name1);
                module_file.put(name, file); //Module corresponding to the file, used to compute the fitness function
//                if (!reflexion_file_list.contains(name1)){
//                    reflexion_file_list.add(name1);
//                }
            }
            combineResultMap.putAll(module_file);
            combineResultMap.putAll(sub_module_file);
        }


        return combineResultMap;

    }


    public void targetModel(String tar_json) {
        //String jsonPath = "E:\\Refactoring\\OptJava-master\\HW10 - NSGA2\\src\\main\\java\\hr\\fer\\zemris\\optjava\\dz10\\nsga\\refactoring\\input\\depends.con.json";
        TargetModel targetModel = JsonUtil.getGSONObject3(new File(tar_json));
        List<String> packages_list = targetModel.getVariables();
        HashMap<Integer, String> packageNum = new HashMap<>();
        int i = 0;
        for (String ppackage : packages_list) {
            packageNum.put(i, ppackage);
            i = i + 1;
        }
        for (String module:targetModel.getVariables()){
            List<String>list=new ArrayList<>();
            module_file.put(module,list);
        }
        //HashMap<String,List<String>> target_model_dependencies=new HashMap<>();
        List<CellsDTO> cellsDTOS = targetModel.getCells();
        for (CellsDTO cellsDTO : cellsDTOS) {
            Integer src = cellsDTO.getSrc();
            Integer dest = cellsDTO.getDest();
            String Src = packageNum.get(src);
            String Dest = packageNum.get(dest);
            List<String> list;
            if (target_model_dependencies.containsKey(Src)) {
                list = target_model_dependencies.get(Src);
            } else {
                list = new ArrayList<>();
            }
            list.add(Dest);
            target_model_dependencies.put(Src, list);
        }

    }

    public void targetModel1(String tar_json) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(new File(tar_json)), "UTF-8"));
        String lineTxt = null;
        while ((lineTxt = br.readLine()) != null) {
            String[] arr = lineTxt.split(",");
            String Src = arr[0];
            String Dest = arr[1];
            List<String> list;
            if (target_model_dependencies.containsKey(Src)) {
                list = target_model_dependencies.get(Src);
            } else {
                list = new ArrayList<>();
            }
            list.add(Dest);
            target_model_dependencies.put(Src, list);
        }

    }


}
