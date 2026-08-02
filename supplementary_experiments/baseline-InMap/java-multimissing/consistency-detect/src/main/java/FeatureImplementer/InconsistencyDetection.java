package FeatureImplementer;

import DataProcessor.TargetDependencies;
import entity.Storage;

import java.util.*;

public class InconsistencyDetection {
    public HashMap<String, List<String>> module2file = new HashMap<String, List<String>>();
    public HashMap<String, List<String>> file2entity = new HashMap<String, List<String>>();
    public List<Integer> inconsistency(Storage read_json) {
        long t1 = System.currentTimeMillis();
        HashMap<String, String> entityFile = read_json.entity_file;
//        HashMap<String,List<String>> target_model_dependencies=read_json.targetModel();
        HashMap<String, List<String>> target_model_dependencies = read_json.target_model_dependencies;
//        Set<String> target_module_list = new HashSet<>();
//        Set<String> target_module_from_list = new HashSet<>();
//        for (String target_from_module : target_model_dependencies.keySet()) {
//            target_module_list.add(target_from_module);
//            target_module_from_list.add(target_from_module);
//            for (String target_to_module : target_model_dependencies.get(target_from_module)) {
//                if (!target_module_list.contains(target_to_module)) {
//                    target_module_list.add(target_to_module);
//                }
//            }
//        }
        HashMap<String, List<String>> dependencies = read_json.dependencies;
//        HashMap<String, List<String>> code_file_dependencies = new HashMap<>();
//        for (String from_entity : dependencies.keySet()) {
//            for (String to_entity : dependencies.get(from_entity)) {
//                String from_entity_file = entityFile.get(from_entity);
//                String to_entity_file = entityFile.get(to_entity);
//                if ((from_entity_file == null) || (to_entity_file == null)) {
//                    String flag = "problem";
//                }
//                if (code_file_dependencies.keySet().contains(from_entity_file)) {
//                    List<String> list = code_file_dependencies.get(from_entity_file);
//                    if (!list.contains(to_entity_file)) {
//                        list.add(to_entity_file);
//                    }
//
//                    code_file_dependencies.put(from_entity_file, list);
//                } else {
//                    List<String> list = new ArrayList<>();
//                    list.add(to_entity_file);
//                    code_file_dependencies.put(from_entity_file, list);
//                }
//            }
//        }
        HashMap<String, List<String>> Module_file = read_json.module_file;
        HashMap<String, List<String>> file_Module = new HashMap<String, List<String>>();
        List<String>test=new ArrayList<>();
        HashMap<String, List<String>>test1=new HashMap<>();
        for (String module : Module_file.keySet()) {
            for (String file : Module_file.get(module)) {
                if (file.contains("src/main/java/depends/extractor/java/JavaImportLookupStrategy.java")){
                    int flag=0;
                }
                if ((!file.contains("src/main/java"))||(!module.contains("src/main/java"))){
                    continue;
                }

                String file1=file.substring(file.indexOf("src/main/java"),file.length());

                String module1=module.substring(module.indexOf("src/main/java")+14,module.length());
                if (!file_Module.containsKey(file1)) {
                    List<String> list = new ArrayList<String>();
                    list.add(module1);
                    file_Module.put(file1, list);
                } else {
                    List<String> list = file_Module.get(file1);
                    list.add(module1);
                    file_Module.put(file1, list);
                    if (!test.contains(file1)){
                        test.add(file1);
                    }


                }
            }
        }


        /*
        for (String file:test){
            boolean b=false;
            for (String m:file_Module.get(file)){
                if (m.contains("org")){
                    b=true;
                }
            }
            if (b==false){
                test1.put(file,file_Module.get(file));
            }


        }
        int len = test.size();
        String[] arr = new String[len];

        for(int i = 0; i < len; i++) {
            arr[i] = test.get(i);

        }

        Arrays.sort(arr);

         */
        HashMap<String, Set<String>> target_model_dependencies_total = TargetDependencies.target_model_dependencies_total;
        Set<String> target = new HashSet<String>();
        for (String fromeModule : target_model_dependencies_total.keySet()) {
            for (String toModule : target_model_dependencies_total.get(fromeModule)) {
                target.add(fromeModule + "->" + toModule);
            }
        }

        List<List<String>> stringList1=new ArrayList<>();
        for (String fromEntity : dependencies.keySet()) {

            if (fromEntity.equals("org.apache.hadoop.mapred.HistoryViewer.printFailedAttempts")) {
                int flag = 0;
            }
            for (String toEntity : dependencies.get(fromEntity)) {
                boolean flag = false;
                String fromFile = entityFile.get(fromEntity);
                String toFile = entityFile.get(toEntity);
                if ((fromFile.equals("Super-Simple-Tasker-main/sst0_c/examples/blinky_button/bsp_ek-tm4c123gxl.c"))&&(toFile.equals("Super-Simple-Tasker-main/sst_c/examples/blinky_button/blinky1.c"))){
                    int f=1;
                }
                List<String> fromModuleList = file_Module.get(fromFile);
                List<String> toModuleList = file_Module.get(toFile);
                if ((fromModuleList == null) || (toModuleList == null)) {
                    continue;
                }
                List<Boolean> booleanList=new ArrayList<>();
                List<String> stringList=new ArrayList<>();
                boolean flag1;
                boolean flag2=false;
                for (String fromModule : fromModuleList) {
                    for (String toModule : toModuleList) {
                        /* enre
                        if ((fromModule.contains("3rd_party"))||(toModule.contains("3rd_party"))){
                            flag=true;
                        }
                        if(!fromModule.contains("include")){
                            flag=true;
                        }

                         */

                        if ((target.contains(fromModule + "->" + toModule)) || (fromModule.equals(toModule))) {
                            flag = true;
                            flag1=true;
                            booleanList.add(true);
                        }
                        else {
                            flag1=false;
                            booleanList.add(false);
                        }
                        //stringList.add(flag1+": "+fromModule+"->"+toModule+"       "+fromFile+"->"+toFile);
                    }
                }

                /*
                if ((booleanList.contains(true))&&(booleanList.contains(false))){
                    int f=1;
                    if (!stringList1.contains(stringList)){
                        stringList1.add(stringList);
                    }

                }
                if (stringList1.size()!=0){
                    int a=1;
                }

                 */

                if (flag == false) {
                    String fromModule = fromModuleList.get(0);
                    String toModule = toModuleList.get(0);
                    if (module2file.containsKey(fromModule + "->" + toModule)) {
                        List<String> list = module2file.get(fromModule + "->" + toModule);
                        if (!list.contains(fromFile + "->" + toFile)) {
                            list.add(fromFile + "->" + toFile);
                        }
                    } else {
                        List<String> list = new ArrayList<String>();
                        list.add(fromFile + "->" + toFile);
                        module2file.put(fromModule + "->" + toModule, list);
                    }
                    if (file2entity.containsKey(fromFile + "->" + toFile)) {
                        List<String> list = file2entity.get(fromFile + "->" + toFile);
                        if (!list.contains(fromEntity + "->" + toEntity)) {
                            list.add(fromEntity + "->" + toEntity);
                        }
                    } else {
                        List<String> list = new ArrayList<String>();
                        list.add(fromEntity + "->" + toEntity);
                        file2entity.put(fromFile + "->" + toFile, list);
                    }
                }
            }
        }
        List<Integer> inconsisit = new ArrayList<Integer>();
        inconsisit.add(module2file.size());
        int i = 0;
        for (String f : file2entity.keySet()) {
            List<String> e = file2entity.get(f);
            i += e.size();
        }
        inconsisit.add(i);
        return inconsisit;

    }
}
