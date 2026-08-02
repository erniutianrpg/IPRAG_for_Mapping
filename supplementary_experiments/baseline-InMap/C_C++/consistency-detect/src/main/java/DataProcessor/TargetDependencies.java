package DataProcessor;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class TargetDependencies {

    public static HashMap<String, Set<String>> target_model_dependencies_total=new HashMap<>();



    public HashMap<String,Set<String>> run(HashMap<String, List<String>> target_model_dependencies){
        Set<String> target_module_list=new HashSet<>();
        Set<String> target_module_from_list=new HashSet<>();
        for (String target_from_module:target_model_dependencies.keySet()){
            target_module_list.add(target_from_module);
            target_module_from_list.add(target_from_module);
            for (String target_to_module:target_model_dependencies.get(target_from_module)){
                if (!target_module_list.contains(target_to_module)){
                    target_module_list.add(target_to_module);
                }
            }
        }
        /* enre
        for (String module:module_file.keySet()){
            if (!target_module_list.contains(module)){
                target_module_list.add(module);
            }
        }

         */
        HashMap<String, Set<String>> super_module=new HashMap<>();
        for (String moduleA:target_module_list){
            Set<String>set=new HashSet<>();
            set.add(moduleA);
            super_module.put(moduleA,set);
        }
        for (String moduleA:target_module_list){
            for (String moduleB:target_module_list){
                /* enre
                List<String> moduleA1 = Arrays.asList(moduleA.split("/"));
                List<String> moduleA2 = Arrays.asList(moduleB.split("/"));
                if (!moduleA1.get(1).equals(moduleA2.get(1))){
                    continue;
                }

                 */
                if ((!moduleA.equals(moduleB))&&(moduleA.startsWith(moduleB))){//&&(moduleA.indexOf(moduleB)!=-1)){
                    Set<String>set=super_module.get(moduleA);
                    set.add(moduleB);
                    super_module.put(moduleA,set);
                }
            }
        }

        //HashMap<String,Set<String>> target_model_dependencies_total= new HashMap<>();
        for (String moduleA:target_module_list) {
            Set<String> moduleA_super_list = super_module.get(moduleA);
            for (String moduleB : target_module_list) {
                if ((moduleA.equals("Super-Simple-Tasker-main/sst0_cpp/src"))&&(moduleB.equals("Super-Simple-Tasker-main/include"))){
                    int f=1;
                }
                Set<String> moduleB_super_list = super_module.get(moduleB);
                for (String moduleA_super : moduleA_super_list) {
                    for (String moduleB_super : moduleB_super_list) {
                        if ((target_module_from_list.contains(moduleA_super)) && (target_model_dependencies.get(moduleA_super)).contains(moduleB_super)) {

                            if (target_model_dependencies_total.keySet().contains(moduleA)) {
                                Set<String> set = target_model_dependencies_total.get(moduleA);
                                set.add(moduleB);
                                target_model_dependencies_total.put(moduleA, set);
                            } else {
                                Set<String> set = new HashSet<>();
                                set.add(moduleB);
                                target_model_dependencies_total.put(moduleA, set);
                            }
                            continue;
                        }
                    }
                }
            }
        }
        return target_model_dependencies_total;
    }
}
