import infer_networks
import analyze_networks
import modularity_over_time
import community_detection_analysis
import corr_par_corr_comparison
from os import makedirs

input_name = "sectors_main.csv"
workfiles_folder = "workfiles/"
cor_dir = workfiles_folder + "corr/"
pcor_dir = workfiles_folder + "par_corr/"
output_destination = "result/"

if __name__ == "__main__":
    #makedirs(output_destination, exist_ok=True)
    #makedirs(cor_dir+"np/", exist_ok=True)
    #makedirs(pcor_dir+"np/", exist_ok=True)
    infer_networks.run(input_name=input_name, cor_dir=cor_dir, pcor_dir=pcor_dir, output_dest=output_destination, workdir=workfiles_folder)
    analyze_networks.run(input_name=input_name, cor_dir=cor_dir, pcor_dir=pcor_dir, output_dest=output_destination, workdir=workfiles_folder)
    modularity_over_time.run(input_name=input_name, cor_dir=cor_dir, pcor_dir=pcor_dir, output_dest=output_destination, workdir=workfiles_folder)
    community_detection_analysis.run(input_name=input_name, cor_dir=cor_dir, pcor_dir=pcor_dir, output_dest=output_destination, workdir=workfiles_folder)
    corr_par_corr_comparison.run(input_name=input_name, cor_dir=cor_dir, pcor_dir=pcor_dir, output_dest=output_destination, workdir=workfiles_folder)
