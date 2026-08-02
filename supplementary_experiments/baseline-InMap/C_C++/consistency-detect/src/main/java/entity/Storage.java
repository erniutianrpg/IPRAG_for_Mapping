package entity;


import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Storage implements Cloneable{
    public HashMap<String, String> entity_file;
    public HashMap<String, String> entity_type;
    public List<String> field_classVar;
    public List<String> field_instanceVar;
    public List<String> func_individual;
    public List<String> func_individual_public;
    public List<String> func_notOverride;
    public List<String> field_type;
    public List<String> func_type;
    public List<String> staticMethod;
    public List<String> abstractClass;
    public HashMap<String, List<String>> module_file;
    //public static List<String> reflexion_file_list =new ArrayList<>(); //the related items have all been commented out
    public HashMap<String, List<String>> dependencies;
    public HashMap<String, List<String>> target_model_dependencies;

    public HashMap<String, List<String>> class_func;

    public HashMap<String, List<String>> class_field;
    public HashMap<String, List<String>> super_subs_class;
    public HashMap<String, String> sub_super_class;
    public HashMap<String, List<String>> method_localVar;
    public HashMap<String, List<String>> class_allMethod;
    public HashMap<String, List<String>> class_allVar;
    public HashMap<String, List<String>> method_parameter_target;
    public HashMap<String, List<String>> field_refenced_target;
    public HashMap<String, List<String>> create_dep;
    public HashMap<String, List<String>> return_dep ;
    public HashMap<String, List<String>> extend_dep;
    public HashMap<String, List<String>> dependencies_reverse;


    public HashMap<String, List<String>> sub_supers_class_implement;
    public List<String> innerClassList;


    public Storage(HashMap<String, List<String>> super_subs_class, HashMap<String, String> sub_super_class,
                   HashMap<String, List<String>> module_file, HashMap<String, List<String>> class_func,
                   HashMap<String, List<String>> class_field, List<String> field_type, List<String> func_type,
                   HashMap<String, List<String>> dependencies, HashMap<String, String> entity_file,
                   List<String> field_classVar, List<String> field_instanceVar, List<String> func_individual,
                   List<String> func_individual_public, List<String> func_notOverride, HashMap<String, String> entity_type,
                   HashMap<String, List<String>> target_model_dependencies, HashMap<String, List<String>> method_localVar,
                   HashMap<String, List<String>> class_allMethod, HashMap<String, List<String>> class_allVar,
                   HashMap<String, List<String>> method_parameter_target, HashMap<String, List<String>> field_refenced_target,
                   HashMap<String, List<String>> dependencies_reverse,  HashMap<String, List<String>> create_dep, HashMap<String, List<String>> return_dep,
                   HashMap<String, List<String>> extend_dep, HashMap<String, List<String>> sub_supers_class_implement,
                   List<String>innerClassList,List<String> staticMethod,List<String> abstractClass
    ) {
        this.super_subs_class = super_subs_class;
        this.sub_super_class = sub_super_class;
        this.module_file = module_file;
        this.class_func = class_func;
        this.class_field = class_field;
        this.field_type = field_type;
        this.func_type = func_type;
        this.dependencies = dependencies;
        this.entity_file = entity_file;
        this.field_classVar = field_classVar;
        this.field_instanceVar = field_instanceVar;
        this.func_individual = func_individual;
        this.func_individual_public = func_individual_public;
        this.func_notOverride = func_notOverride;
        this.entity_type = entity_type;
        this.target_model_dependencies = target_model_dependencies;
        this.method_localVar = method_localVar;
        this.class_allMethod = class_allMethod;
        this.class_allVar = class_allVar;
        this.method_parameter_target = method_parameter_target;
        this.field_refenced_target = field_refenced_target;
        this.dependencies_reverse = dependencies_reverse;
        this.create_dep = create_dep;
        this.return_dep=return_dep;
        this.extend_dep=extend_dep;
        this.sub_supers_class_implement = sub_supers_class_implement;
        this.innerClassList=innerClassList;
        this.staticMethod=staticMethod;
        this.abstractClass = abstractClass;
    }

    @Override
    public Storage clone() {
        try {
            Storage cloned = (Storage) super.clone();
            cloned.entity_file = new HashMap<>(entity_file);
            cloned.entity_type = new HashMap<>(entity_type);
            cloned.field_classVar = new ArrayList<>(field_classVar);
            cloned.field_instanceVar = new ArrayList<>(field_instanceVar);
            cloned.func_individual = new ArrayList<>(func_individual);
            cloned.func_individual_public = new ArrayList<>(func_individual_public);
            cloned.func_notOverride = new ArrayList<>(func_notOverride);
            cloned.field_type = new ArrayList<>(field_type);
            cloned.func_type = new ArrayList<>(func_type);
            cloned.staticMethod = new ArrayList<>(staticMethod);
            cloned.abstractClass = new ArrayList<>(abstractClass);
            cloned.module_file = deepCopyHashMapOfLists(module_file);
            cloned.dependencies = deepCopyHashMapOfLists(dependencies);
            cloned.target_model_dependencies = deepCopyHashMapOfLists(target_model_dependencies);
            cloned.class_func = deepCopyHashMapOfLists(class_func);
            cloned.class_field = deepCopyHashMapOfLists(class_field);
            cloned.super_subs_class = deepCopyHashMapOfLists(super_subs_class);
            cloned.sub_super_class = new HashMap<>(sub_super_class);
            cloned.method_localVar = deepCopyHashMapOfLists(method_localVar);
            cloned.class_allMethod = deepCopyHashMapOfLists(class_allMethod);
            cloned.class_allVar = deepCopyHashMapOfLists(class_allVar);
            cloned.method_parameter_target = deepCopyHashMapOfLists(method_parameter_target);
            cloned.field_refenced_target = deepCopyHashMapOfLists(field_refenced_target);
            cloned.create_dep = deepCopyHashMapOfLists(create_dep);
            cloned.return_dep = deepCopyHashMapOfLists(return_dep);
            cloned.extend_dep = deepCopyHashMapOfLists(extend_dep);
            cloned.dependencies_reverse = deepCopyHashMapOfLists(dependencies_reverse);

            cloned.sub_supers_class_implement = deepCopyHashMapOfLists(sub_supers_class_implement);


            cloned.innerClassList = new ArrayList<>(innerClassList);

            return cloned;
        } catch (CloneNotSupportedException e) {
            throw new AssertionError("Cloning failed.", e);
        }}
    private <K> HashMap<K, List<String>> deepCopyHashMapOfLists(HashMap<K, List<String>> original) {
        HashMap<K, List<String>> copy = new HashMap<>();
        for (Map.Entry<K, List<String>> entry : original.entrySet()) {
            copy .put(entry.getKey(), new ArrayList<>(entry.getValue()));
        }
        return copy;
    }
}
