package client;

import DataProcessor.DataConversion;
import DataProcessor.ReflectionModelBuilder;
import FeatureImplementer.InconsistencyDetection;
import Model.Dependency.DependencyData;
import Model.JsonUtil;
import Model.Reflexion.ReflectionModel;
import ReflexionModel.SimilarityScore;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.alibaba.fastjson.serializer.SerializerFeature;
import entity.Storage;
import org.apache.lucene.queryparser.classic.ParseException;

import java.io.File;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException, ParseException {

        String jarName = "E:/Architecture/InconsistencyDetect/enre-java-locations.jar";
        String lang = "java";
        String rootDir = "E:/Refactoring/HW-refactorAll/project/depends";
        String projectName = "depends";

        generateDep(jarName, lang, rootDir, projectName);

        int lastBackslashIndex = jarName.lastIndexOf("/");
        String dep_Jsondir = jarName.substring(0, lastBackslashIndex) + "/" + projectName + "-ja-out/" + projectName + "-out.json";
        DependencyData dependencyData = JsonUtil.getGSONObject1(new File(dep_Jsondir));


        //Automatic reflexion-model generation based on text matching
//        SimilarityScore.run();

        //Automatic reflexion-model generation based on the directory structure by Jingwen
        ReflectionModelBuilder reflectionModelBuilder=new ReflectionModelBuilder();
        ReflectionModel reflectionModel1=reflectionModelBuilder.buildReflectionModel("1.0","E:\\Architecture\\InconsistencyDetect\\inmap-seed-mapping-main\\data\\architectures\\ant");

        //Automatic reflexion-model generation based on the directory structure by Junhui
        //        generateRfx(jarName, rootDir, projectName);

        String rfx_Jsondir = jarName.substring(0, lastBackslashIndex) + "/" + projectName + "-ja-out/" + projectName + ".rfx.json";
        ReflectionModel reflectionModel = JsonUtil.getGSONObject2(new File(rfx_Jsondir));


        HashMap<String, List<String>> target_model_dependencies = readTarget();

        DataConversion dataConversion=new DataConversion();
        Storage storage=dataConversion.run(dep_Jsondir,rfx_Jsondir,target_model_dependencies);

        InconsistencyDetection fitnessfunction = new InconsistencyDetection();
        List<Integer>inconsist = fitnessfunction.inconsistency(storage);
        int initialInconsist = 0;
        for (Integer inconsistD : inconsist) {
            initialInconsist += inconsistD;
        }
        if (initialInconsist == 0) {
//            JsonRootBean jsonRootBean = Write_json.refactoringWriter();
//            JsonUtil.outputDependencyDataToFile(jsonRootBean, new File(out_json));
            return;
        }
        HashMap<String, List<String>> module2file = fitnessfunction.module2file;
        HashMap<String, List<String>> file2entity = fitnessfunction.file2entity;
        Set<String> moduleInconsist = module2file.keySet();
        Set<String> fileInconsist=file2entity.keySet();
        Set<String> entityInconsist = new HashSet<>();
        for (String key : file2entity.keySet()) {
            entityInconsist.addAll(file2entity.get(key));
        }
        int flag=0;

    }

    private static HashMap<String, List<String>> readTarget() throws IOException {
        String filePath = "E:\\Architecture\\InconsistencyDetect\\depends-ja-out/depends.con.plantuml";
        HashMap<String, List<String>> target_model_dependencies = new HashMap<>();

        try {
            List<String> lines = Files.readAllLines(Paths.get(filePath));
            Map<String, String> idToComponent = new HashMap<>();

            // First pass: find all components and record their  ID
            for (String line : lines) {
                line = line.trim();
                if (line.startsWith("component")) {
                    String[] parts = line.split("\"");
                    String component = parts[1];
                    String id = parts[2].split("as")[1].trim();
                    idToComponent.put(id, component);
                }
            }

            // Second pass: find and record all dependencies
            for (String line : lines) {
                line = line.trim();
                if (line.contains("-->")) {
                    String[] parts = line.split("-->");
                    String srcId = parts[0].trim();
                    String destId = parts[1].trim();

                    // If the source or target  ID is not in our mapping, skip this line
                    if (!idToComponent.containsKey(srcId) || !idToComponent.containsKey(destId)) {
                        continue;
                    }

                    String srcComponent = idToComponent.get(srcId);
                    String destComponent = idToComponent.get(destId);

                    // If this source component is not yet in our dependency graph, add it
                    if (!target_model_dependencies.containsKey(srcComponent)) {
                        target_model_dependencies.put(srcComponent, new ArrayList<>());
                    }

                    // Add the target component to the source component's dependency list
                    target_model_dependencies.get(srcComponent).add(destComponent);
                }
            }
        }catch (IOException e) {
            e.printStackTrace();
        }

/* Check whether it is consistent with the original target model, and generate the corresponding plantuml
        HashMap<String, Set<String>> target_model_dependencies1 = new HashMap<>();
        TargetModel targetModel = JsonUtil.getGSONObject3(new File("E:/Refactoring/HW-refactorAll/archeranalysis/depends/depends.con.json"));
        List<String> packages_list = targetModel.getVariables();
        HashMap<Integer, String> packageNum = new HashMap<>();
        int i = 0;
        for (String ppackage : packages_list) {
            packageNum.put(i, ppackage);
            i = i + 1;
        }
        //HashMap<String,List<String>> target_model_dependencies=new HashMap<>();
        List<CellsDTO> cellsDTOS = targetModel.getCells();
        for (CellsDTO cellsDTO : cellsDTOS) {
            Integer src = cellsDTO.getSrc();
            Integer dest = cellsDTO.getDest();
            String Src = packageNum.get(src);
            String Dest = packageNum.get(dest);
            Set<String> list;
            if (target_model_dependencies1.containsKey(Src)) {
                list = target_model_dependencies1.get(Src);
            } else {
                list = new HashSet<>();
            }
            list.add(Dest);
            target_model_dependencies1.put(Src, list);
        }

        generatePlantUML(target_model_dependencies1);
        compareMaps(target_model_dependencies,target_model_dependencies1);


 */
        return target_model_dependencies;

    }

    //maprecords dependencies and generates plantumlformat
    public static void generatePlantUML(HashMap<String, Set<String>> map) throws IOException {
        StringBuilder plantUML = new StringBuilder("@startuml\n\n");
        HashMap<String, String> components = new HashMap<>();

        int i = 1;
        for (String key : map.keySet()) {
            if (!components.containsKey(key)) {
                components.put(key, "v" + i);
                i++;
            }

            for (String value : map.get(key)) {
                if (!components.containsKey(value)) {
                    components.put(value, "v" + i);
                    i++;
                }
            }
        }

        for (Map.Entry<String, String> entry : components.entrySet()) {
            plantUML.append("component \"").append(entry.getKey()).append("\" as ").append(entry.getValue()).append("\n");
        }

        plantUML.append("\n");

        for (Map.Entry<String, Set<String>> entry : map.entrySet()) {
            String key = entry.getKey();
            for (String value : entry.getValue()) {
                plantUML.append(components.get(key)).append(" --> ").append(components.get(value)).append("\n");
            }
        }

        plantUML.append("\n@enduml");

        FileWriter writer = new FileWriter("E:\\Architecture\\InconsistencyDetect\\depends-ja-out/depends.con.plantuml");
        writer.write(plantUML.toString());
        writer.close();
    }
    public static void compareMaps(Map<String, Set<String>> map1, Map<String, Set<String>> map2) {
        for (String key : map1.keySet()) {
            if (!map2.containsKey(key)) {
                System.out.println("Key '" + key + "' found in map1 but not in map2");
            } else if (!map1.get(key).equals(map2.get(key))) {
                System.out.println("Value for key '" + key + "' different between maps: map1 = " + map1.get(key) + ", map2 = " + map2.get(key));
            }
        }

        for (String key : map2.keySet()) {
            if (!map1.containsKey(key)) {
                System.out.println("Key '" + key + "' found in map2 but not in map1");
            }
        }
    }

    private static void generateRfx(String jarName,String rootDir, String projectName) throws IOException {
        //Specify the target file directory
        /*
        Scanner scan=new Scanner(System.in);//Console input control
        System.out.println("Please enter");//Prompt for input
        String str=scan.nextLine();  //nextLine()receives string input
        System.out.println("Target project path: "+str);//Output the value just entered
//        String rootDir =  str;
         */
        //Createjsonformat
        JSONObject object = new JSONObject();
        object.put("@schemaVersion","1.0");
        object.put("name","clustering");
        JSONArray structures=new JSONArray();
        //Recursively scan project files
        String[] rootPath=rootDir.split("/");
        int len=rootPath.length;
        findFiles(rootDir,len,structures);
        object.put("structure",structures);
        //Outputjsonfile,the parent directory of the target project file
        String outPath=rootPath[0];
        for (int i=1;i<len-1;i++){
            outPath=outPath+"/"+rootPath[i];
        }
//        outPath=outPath+"/"+rootPath[len-1]+"-output.json";
        int lastBackslashIndex = jarName.lastIndexOf("/");
        outPath=jarName.substring(0, lastBackslashIndex)+"/"+projectName+"-ja-out/"+projectName+".rfx.json";
        System.out.println("outpath:"+outPath);
        File file = new File(outPath);
        //Check whether the path exists; create it if it does not
        if(!file.getParentFile().exists()){
            file.getParentFile().mkdir();
        }
        //Convert format
        String jsonString = JSON.toJSONString(object, SerializerFeature.PrettyFormat, SerializerFeature.WriteMapNullValue,
                SerializerFeature.WriteDateUseDateFormat);
        Writer writer = new OutputStreamWriter(new FileOutputStream(file),"UTF-8");
        writer.write(jsonString);
        writer.flush();
        writer.close();
    }
    public static JSONObject findFiles(String path,int pathLen,JSONArray structures){
        File file = new File(path);
        if (file.isDirectory()) {
            //Split the absolute path and store the relative path.
            String[] pathStrlist=path.split("/");
            String pathStr=pathStrlist[pathLen-1];
            for (int i=pathLen;i<pathStrlist.length;i++){
                pathStr=pathStr+"/"+pathStrlist[i];
            }
            System.out.println("Reading " + pathStr + "directory....");
            String[] list = file.list();
            //Add the current folder
            JSONObject dir=new JSONObject();
            dir.put("@type","group");
            dir.put("name",pathStr);
            JSONArray nested=new JSONArray();
            //When a folder contains both files and subfolders, add thisfolder
            JSONArray nestedthis=new JSONArray();
            //When there are only files, directly nestedadd it.
            Boolean hasDir=false;
            for (int i = 0; i < list.length; i++) {
                File file2 = new File(path + "/" + list[i]);
                if (file2.isDirectory()) {
                    hasDir=true;
                    System.out.println("Folder: " + list[i]);
//                    nested.add(findFiles(path + "\\" + list[i],nested));
                    findFiles(path + "/" + list[i],pathLen,nested);
                } else {
                    String[] filename=list[i].split("\\.");
                    int len=filename.length;
                    if(filename[len-1].equals("java")){
                        System.out.println("File: " + list[i]);
                        JSONObject fileJson=new JSONObject();
                        fileJson.put("@type","item");
                        fileJson.put("name",pathStr+"/"+list[i]);
                        fileJson.put("rawName",pathStr+"/"+list[i]);
                        nestedthis.add(fileJson);
                    }
                }
            }
            if(nestedthis.size()>0 && hasDir) {
                JSONObject dirthis=new JSONObject();
                dirthis.put("@type","group");
                dirthis.put("name",pathStr+"/"+"this");
                dirthis.put("nested",nestedthis);
                nested.add(dirthis);
            }
            if(!hasDir){
                for (int i = 0; i < list.length; i++) {
                    File file2 = new File(path + "/" + list[i]);
                    if (!file2.isDirectory()) {
                        String[] filename = list[i].split("\\.");
                        int len = filename.length;
//                        if (filename[len - 1].equals("c") || filename[len - 1].equals("cpp")|| filename[len - 1].equals("h")|| filename[len - 1].equals("hpp")) {
                        if (filename[len - 1].equals("java")) {
                            System.out.println("File: " + list[i]);
                            JSONObject fileJson = new JSONObject();
                            fileJson.put("@type", "item");
                            fileJson.put("name", pathStr + "/" + list[i]);
                            fileJson.put("rawName", pathStr + "/" + list[i]);
                            nested.add(fileJson);
                        }
                    }
                }
            }
            dir.put("nested",nested);
            //Do not add empty entries
            if(nested.size()>0)
            structures.add(dir);
            return dir;
        } else {
            System.out.println(path + " is not a directory.");
            return null;
        }
    }

    private static void generateDep(String jarName, String lang, String rootDir, String projectName) throws IOException {
        ProcessBuilder pb = new ProcessBuilder("java", "-jar", jarName, lang, rootDir, projectName, "-j");
        Process process = pb.start();
        InputStream inputStream = process.getInputStream();
        BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
        StringBuilder output = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            output.append(line);
            output.append("\n");
        }

        System.out.println("Output: " + output.toString());

    }
}
