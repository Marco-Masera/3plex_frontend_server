from django.core.files import File
from .models import *
from triplex_frontend.triplex_exceptions import *
from datetime import datetime
from django.conf import settings
from django.db.models import Q
from django.core.files.temp import NamedTemporaryFile
import os

class PromoterStabilityTestServices:
    def initialize_data_section(ssRNA_fasta, ssRNA_id, all_genes, interest_genes, species, triplex_params):
        #Compute hash value of input data
        triplex_params_stringified = {}
        for k in triplex_params.keys():
            triplex_params_stringified[k] = str(triplex_params[k])
        #initialize new data section, keep track of sequence and id, used later for computing the conservation
        job = StabilityTestJobData()
        job.triplex_params = triplex_params
        job.save() #To generate id
        if (ssRNA_id is not None):
            try:
                longestTranscript = LongestTranscript.objects.get(id=ssRNA_id)
                job.ssRNA_id = longestTranscript
            except LongestTranscript.DoesNotExist:
                raise SsRnaIdNotValidException()
        else:
            job.ssRNA_id = None
        if (ssRNA_fasta is not None):
            job.ssRNA_fasta = ssRNA_fasta
            job.ssRNA_fasta.name = f"jobs/{job.base_path}/{settings.SSRNA_BASE_NAME}"
        #Save on file the genes
        base_path = settings.MEDIA_ROOT
        os.mkdir(f"{base_path}/jobs/{job.base_path}")

        all_genes_file = NamedTemporaryFile(delete=True)
        with open(all_genes_file.name, 'w') as f:
            f.write("\n".join(all_genes))
        all_genes_file.flush()
        job.genes_all = File(all_genes_file, name=f"jobs/{job.base_path}/genes_all")

        genes_of_interest_file = NamedTemporaryFile(delete=True)
        with open(genes_of_interest_file.name, 'w') as f:
            f.write("\n".join(interest_genes))
        genes_of_interest_file.flush()
        job.genes_of_interest = File(genes_of_interest_file, name=f"jobs/{job.base_path}/genes_of_interests")
       
        job.species = species
        job.save()
        return job

    def set_job_submitted(job: StabilityTestJobData):
        job.state = "Submitted"
        job.save()
    
    def cleanup_old_jobs(cleanup_older_than):
        old_jobs = StabilityTestJobData.objects.filter(date__lte=cleanup_older_than, cleaned_up = False)
        for old_job in old_jobs:
            old_job.state = "Expired"
            old_job.delete_all_files()
            old_job.cleaned_up = True
            old_job.save()

    def set_job_failed(job, stdout, stderr):
        jobObject.state = "Failed"
        if (STDOUT is not None):
            jobObject.rawLogsSTDOUT = STDOUT
            jobObject.rawLogsSTDOUT.name = f"jobs/{jobObject.base_path}/Logs_STDOUT"
        if (STDERR is not None):
            jobObject.rawLogsSTDERR = STDERR
            jobObject.rawLogsSTDERR.name = f"jobs/{jobObject.base_path}/Logs_STDERR"
        jobObject.save()

    def receive_data(*args):
        data, stability, summary, STABILITY_BEST, STABILITY_NORM, STABILITY_BEST_FGSEA_RES, STABILITY_BEST_LEADING_EDGE, STABILITY_BEST_ENRICHMENT_PLOT, STABILITY_BEST_STABILITY_COMP_BOXPLOT, STABILITY_BEST_STABILITY_COMP, STABILITY_NORM_FGSEA_RES, STABILITY_NORM_LEADING_EDGE, STABILITY_NORM_ENRICHMENT_PLOT, STABILITY_NORM_STABILITY_COMP_BOXPLOT, STABILITY_NORM_STABILITY_COMP = args 
               
        data.stability = stability
        data.summary = summary
        data.stability.name = f"jobs/{data.base_path}/{data.stability.name}"
        data.summary.name = f"jobs/{data.base_path}/{data.summary.name}"
        # Update STABILITY_BEST
        data.STABILITY_BEST = STABILITY_BEST
        data.STABILITY_BEST.name = f"jobs/{data.base_path}/{data.STABILITY_BEST.name}"
        print(data.STABILITY_BEST.name)
        # Update STABILITY_NORM
        data.STABILITY_NORM = STABILITY_NORM
        data.STABILITY_NORM.name = f"jobs/{data.base_path}/{data.STABILITY_NORM.name}"

        # Update STABILITY_BEST_FGSEA_RES
        data.STABILITY_BEST_FGSEA_RES = STABILITY_BEST_FGSEA_RES
        data.STABILITY_BEST_FGSEA_RES.name = f"jobs/{data.base_path}/{data.STABILITY_BEST_FGSEA_RES.name}"

        # Update STABILITY_BEST_LEADING_EDGE
        data.STABILITY_BEST_LEADING_EDGE = STABILITY_BEST_LEADING_EDGE
        data.STABILITY_BEST_LEADING_EDGE.name = f"jobs/{data.base_path}/{data.STABILITY_BEST_LEADING_EDGE.name}"

        # Update STABILITY_BEST_ENRICHMENT_PLOT
        data.STABILITY_BEST_ENRICHMENT_PLOT = STABILITY_BEST_ENRICHMENT_PLOT
        data.STABILITY_BEST_ENRICHMENT_PLOT.name = f"jobs/{data.base_path}/{data.STABILITY_BEST_ENRICHMENT_PLOT.name}"
        # Update STABILITY_BEST_STABILITY_COMP_BOXPLOT
        data.STABILITY_BEST_STABILITY_COMP_BOXPLOT = STABILITY_BEST_STABILITY_COMP_BOXPLOT
        data.STABILITY_BEST_STABILITY_COMP_BOXPLOT.name = f"jobs/{data.base_path}/{data.STABILITY_BEST_STABILITY_COMP_BOXPLOT.name}"

        # Update STABILITY_BEST_STABILITY_COMP
        data.STABILITY_BEST_STABILITY_COMP = STABILITY_BEST_STABILITY_COMP
        data.STABILITY_BEST_STABILITY_COMP.name = f"jobs/{data.base_path}/{data.STABILITY_BEST_STABILITY_COMP.name}"

        # Update STABILITY_NORM_FGSEA_RES
        data.STABILITY_NORM_FGSEA_RES = STABILITY_NORM_FGSEA_RES
        data.STABILITY_NORM_FGSEA_RES.name = f"jobs/{data.base_path}/{data.STABILITY_NORM_FGSEA_RES.name}"

        # Update STABILITY_NORM_LEADING_EDGE
        data.STABILITY_NORM_LEADING_EDGE = STABILITY_NORM_LEADING_EDGE
        data.STABILITY_NORM_LEADING_EDGE.name = f"jobs/{data.base_path}/{data.STABILITY_NORM_LEADING_EDGE.name}"

        # Update STABILITY_NORM_ENRICHMENT_PLOT
        data.STABILITY_NORM_ENRICHMENT_PLOT = STABILITY_NORM_ENRICHMENT_PLOT
        data.STABILITY_NORM_ENRICHMENT_PLOT.name = f"jobs/{data.base_path}/{data.STABILITY_NORM_ENRICHMENT_PLOT.name}"

        # Update STABILITY_NORM_STABILITY_COMP_BOXPLOT
        data.STABILITY_NORM_STABILITY_COMP_BOXPLOT = STABILITY_NORM_STABILITY_COMP_BOXPLOT
        data.STABILITY_NORM_STABILITY_COMP_BOXPLOT.name = f"jobs/{data.base_path}/{data.STABILITY_NORM_STABILITY_COMP_BOXPLOT.name}"

        # Update STABILITY_NORM_STABILITY_COMP
        data.STABILITY_NORM_STABILITY_COMP = STABILITY_NORM_STABILITY_COMP
        data.STABILITY_NORM_STABILITY_COMP.name = f"jobs/{data.base_path}/{data.STABILITY_NORM_STABILITY_COMP.name}"

        #Set state Ready
        data.state = "Ready"
        data.save()
        return data

    def update_data_last_date(jobData):
        jobData.date = datetime.now()
        jobData.save()

    def get_data(data):
        #Returns urls of available data
        def clean_name(name):
            return name.split("/")[-1]
        available = dict() 
        fields = ['genes_of_interest', 'genes_all', 'rawLogsSTDERR', 'rawLogsSTDOUT', 
        'STABILITY_BEST', 'STABILITY_NORM', 'STABILITY_BEST_FGSEA_RES', 'STABILITY_BEST_LEADING_EDGE',
        'STABILITY_BEST_ENRICHMENT_PLOT', 'STABILITY_BEST_STABILITY_COMP_BOXPLOT', 'STABILITY_BEST_STABILITY_COMP',
        'STABILITY_NORM_FGSEA_RES', 'STABILITY_NORM_LEADING_EDGE', 'STABILITY_NORM_ENRICHMENT_PLOT',
        'STABILITY_NORM_STABILITY_COMP_BOXPLOT', 'STABILITY_NORM_STABILITY_COMP'
        ]
        for variable_name in fields:
            file_field = getattr(data, variable_name)
            if (file_field != None  and bool(file_field)):
                available[clean_name(file_field.name)] = file_field.url
        return available

    def get_triplex_params(job):
        return job.triplex_params