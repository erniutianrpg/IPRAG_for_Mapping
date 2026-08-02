package DataProcessor;

import entity.Storage;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Set;

public class DataConversion {
    public Storage run(String dep_Jsondir,String rfx_Jsondir,HashMap<String, List<String>> target_model_dependencies){
        ReadJson read_json = new ReadJson();
//        read_json.Dependencies_enre(dep_json);
        read_json.resolvePackageFiles(rfx_Jsondir);

        read_json.getMethodFieldInClass(dep_Jsondir);
        read_json.Dependencies(dep_Jsondir);
        read_json.resolveExtendRelation(dep_Jsondir);




        HashMap<String, List<String>> super_subs_class = read_json.super_subs_class;
        HashMap<String, String> sub_super_class = read_json.sub_super_class;
        HashMap<String, List<String>> module_file = read_json.module_file;
        HashMap<String, List<String>> class_func = read_json.class_func;
        HashMap<String, List<String>> class_field = read_json.class_field;
        HashMap<String, List<String>> method_parameter_target = read_json.method_parameter_target;
        HashMap<String, List<String>> fieldRefencedTarget = read_json.field_refenced_target;
        HashMap<String, List<String>> create_dep = read_json.create_dep;
        HashMap<String, List<String>> return_dep = read_json.return_dep;
        HashMap<String, List<String>> extend_dep = read_json.extend_dep;
        List<String> field_type = read_json.field_type;
        List<String> func_type = read_json.func_type;
        HashMap<String, List<String>> dependencies = read_json.dependencies;
        HashMap<String, List<String>> dependencies_reverse = read_json.dependencies_reverse;
        HashMap<String, String> entity_file = read_json.entity_file;
        List<String> field_classVar = read_json.field_classVar;
        List<String> field_instanceVar = read_json.field_instanceVar;
        List<String> func_individual = read_json.func_individual;
        List<String> func_individual_public = read_json.func_individual_public;
        List<String> func_notOverride=read_json.func_notOverride;
        HashMap<String, String> entity_type = read_json.entity_type;
        HashMap<String, List<String>> method_localVar = read_json.method_localVar;
        HashMap<String, List<String>> class_allMethod = read_json.class_allMethod;
        HashMap<String, List<String>> class_allVar = read_json.class_allVar;
        HashMap<String, Integer> entity_line = read_json.entity_line;
        HashMap<String, Integer> entity_row = read_json.entity_row;
        HashMap<String, List<String>> super_class_implement = read_json.sub_supers_class_implement;
        List<String> innerClassList=read_json.innerClassList;
        List<String> staticMethod = read_json.staticMethod;
        List<String> abstractClass = read_json.abstractClass;




        Storage storage = new Storage(super_subs_class, sub_super_class, module_file, class_func,
                class_field, field_type, func_type, dependencies, entity_file,
                field_classVar, field_instanceVar, func_individual, func_individual_public,func_notOverride,
                entity_type, target_model_dependencies, method_localVar, class_allMethod, class_allVar,
                method_parameter_target, fieldRefencedTarget, dependencies_reverse,create_dep,return_dep,extend_dep,super_class_implement,
                innerClassList,staticMethod,abstractClass);

        TargetDependencies targetDependencies = new TargetDependencies();
        targetDependencies.run(target_model_dependencies);

        return storage;
    }
}
