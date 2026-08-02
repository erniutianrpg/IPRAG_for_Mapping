package DataProcessor;

import Model.Reflexion.ReflectionModel;
import Model.Reflexion.StructureDTO;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class ReflectionModelBuilder {
    private static final Set<String> SOURCE_EXTENSIONS = new HashSet<>(Arrays.asList(
            ".java", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"
    ));

    public ReflectionModel buildReflectionModel(String schemaVersion, String rootDirPath) {
        ReflectionModel model = new ReflectionModel();
        model.setSchemaVersion(schemaVersion);
        model.setName(rootDirPath);

        File rootDir = new File(rootDirPath);
        if (rootDir.exists()) {
            model.setStructure(buildStructure(rootDir));
        }

        return model;
    }
    private List<StructureDTO> buildStructure(File dir) {
        List<StructureDTO> structure = new ArrayList<>();
        File[] files = dir.listFiles();
        if (files == null) {
            return structure;
        }
        for (File file : files) {
            if (file.isDirectory()) {
                StructureDTO dto = new StructureDTO();
                dto.setName(file.getPath()); // Set the name as the full path for directories
                dto.setType("group");
                dto.setNested(buildStructure(file));
                structure.add(dto);
            } else if (file.isFile() && isSourceFile(file.getName())) {
                StructureDTO dto = new StructureDTO();
                dto.setName(file.getName()); // Set the name as the file name for files
                dto.setRawName(file.getPath()); // Set raw name for files
                dto.setType("item");
                structure.add(dto);
            }
        }
        return structure;
    }

    private boolean isSourceFile(String fileName) {
        String lowerName = fileName.toLowerCase();
        for (String extension : SOURCE_EXTENSIONS) {
            if (lowerName.endsWith(extension)) {
                return true;
            }
        }
        return false;
    }

//    private List<StructureDTO> buildStructure(File dir) {
//        List<StructureDTO> structure = new ArrayList<>();
//        for (File file : dir.listFiles()) {
//            StructureDTO dto = new StructureDTO();
//            dto.setName(file.getName());
//            dto.setType(file.isDirectory() ? "group" : "item");
//
//            // Set rawName only for files
//            if (file.isFile()) {
//                dto.setRawName(file.getPath()); // or any other logic to derive raw name
//            }
//
//            if (file.isDirectory()) {
//                dto.setNested(buildStructure(file));
//            }
//
//            structure.add(dto);
//        }
//        return structure;
//    }

}
