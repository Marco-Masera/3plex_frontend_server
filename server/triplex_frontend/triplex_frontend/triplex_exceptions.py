from triplex_frontend.responses import Responses
from rest_framework import status
from rest_framework.response import Response
import traceback


def print_error(err):
    print("An error occurred:")
    print(str(err))
    traceback.print_exc()

class TriplexException(Exception):
    def __str__(self):
        return "Generic Triplex Exception"

    def handle(self):
        print_error(self)
        return Responses.generic_failure()

    def __str__(self):
        return "The module is not ready yet on the server side"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(message="The module is not ready yet on the server side")

class SsRnaNotProvidedException(TriplexException):
    def __str__(self):
        return "You need to provide either a ssRNA fasta file as 'SSRNA_FASTA' or an Id as 'SSRNA_ID'"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="You need to provide either a ssRNA fasta file as 'SSRNA_FASTA' or an Id as 'SSRNA_ID'",
            errorCode= status.HTTP_400_BAD_REQUEST)

class SsRnaNoIntestation(TriplexException):
    def __str__(self):
        return "Your ssRNA file does not contain an intestation. It must start with: '>NAME'"

    def handle(self):
        print_error(self)
        return Responses.personalized_failure(
            {
                "message":"Your ssRNA file does not contain an intestation. It must start with: '>NAME'",
                "errorType":"ssRNA_error",
                "whatsWrong": "ssRNA input must follow fasta format and start with an intestation - es >NAME"
            },
            status.HTTP_400_BAD_REQUEST)

class ssRNAGenericError(TriplexException):
    def __init__(self, message):
        super().__init__()
        self.message = message 

    def __str__(self):
        try:
            return f"ssRNA Generic Error: {self.message}"
        except Exception:
            return "ssRNA Generic Error"

    def handle(self):
        print_error(self)
        return Responses.personalized_failure(
            {
                "message":self.message,
                "errorType":"ssRNA_error",
                "whatsWrong": self.message
            },
            status.HTTP_400_BAD_REQUEST)


class dsDNAGenericError(TriplexException):
    def __init__(self, message):
        super().__init__()
        self.message = message 

    def __str__(self):
        try:
            return f"dsDNA Generic Error: {self.message}"
        except Exception:
            return "dsDNA Generic Error"

    def handle(self):
        print_error(self)
        return Responses.personalized_failure(
            {
                "message":self.message,
                "errorType":"dsDNA_error",
                "whatsWrong": self.message
            },
            status.HTTP_400_BAD_REQUEST)

            

class BedFileMalformed(TriplexException):
    def __str__(self):
        return "The provided dsDNA file does not follow the bed format conventions. Make sure the file is in the correct format."

    def handle(self):
        print_error(self)
        return Responses.personalized_failure(
            {
                "message":"The provided dsDNA file does not follow the bed format conventions. Make sure the file is in the correct format.",
                "errorType":"dsDNA_error",
                "whatsWrong": "The provided dsDNA file does not follow the bed format conventions. Make sure the file is in the correct format."
            },
            status.HTTP_400_BAD_REQUEST)

class SsRnaInvalidSequence(TriplexException):
    def __str__(self):
        return "Your ssRNA file contains unrecognized symbols. Only symbols allowed are G, C, T, A."

    def handle(self):
        print_error(self)
        return Responses.personalized_failure(
            {
                "message":"Your ssRNA file contains unrecognized symbols. Only symbols allowed are G, C, T, A.",
                "errorType":"ssRNA_error",
                "whatsWrong": "Your ssRNA file contains unrecognized symbols. Only symbols allowed are G, C, T, A."
            },
            status.HTTP_400_BAD_REQUEST)

class SsRnaMultiline(TriplexException):
    def __str__(self):
        return "The ssRNA.fa file must contain 2 lines: one for intestation, one with the sequence."

    def handle(self):
        print_error(self)
        return Responses.personalized_failure(
            {
                "message":"The ssRNA.fa file must contain 2 lines: one for intestation, one with the sequence.",
                "errorType":"ssRNA_error",
                "whatsWrong": "The ssRNA.fa file must contain 2 lines: one for intestation, one with the sequence."
            },
            status.HTTP_400_BAD_REQUEST)

class SsRnaIdNotValidException(TriplexException):
    def __str__(self):
        return "The longest transcript id provided is not recognized in the system."

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="The longest transcript id provided is not recognized in the system.",
            errorCode= status.HTTP_400_BAD_REQUEST)

class DsDnaNotProvidedException(TriplexException):
    def __str__(self):
        return "You need to provide either a dsDNA fasta file as 'DSDNA_FASTA' or a bed file as 'DSDNA_COORD_BED'"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="You need to provide either a dsDNA fasta file as 'DSDNA_FASTA' or a bed file as 'DSDNA_COORD_BED'",
            errorCode= status.HTTP_400_BAD_REQUEST)

class SpeciesNotProvidedException(TriplexException):
    def __str__(self):
        return "You need to provide a species for the job"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="You need to provide a species for the job",
            errorCode= status.HTTP_400_BAD_REQUEST)
class SpeciesNotSupportedException(TriplexException):
    def __str__(self):
        return "The provided species is not supported."

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="The provided species is not supported.",
            errorCode= status.HTTP_400_BAD_REQUEST)

class NumIterationsNotAllowed(TriplexException):
    def __str__(self):
        return "The provided number of iterations is not allowed."

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="The provided number of iterations is not allowed.",
            errorCode= status.HTTP_400_BAD_REQUEST)

class CannotSubmitToBackendException(TriplexException):
    def __str__(self):
        return "Cannot submit job right now - our HPC is currently too busy. Please try again later."

    def handle(self):
        print_error(self)
        return Responses.generic_failure(message="Cannot submit job right now - our HPC is currently too busy. Please try again later.")

class DataDoesNotExistException(TriplexException):
    def __str__(self):
        return "The requested data does not exist in the system"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="The requested data does not exist in the system",
            errorCode= status.HTTP_404_NOT_FOUND)

class TokenDoesNotExistException(TriplexException):
    def __str__(self):
        return "The requested token does not exist in the system"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="The requested token does not exist in the system",
            errorCode= status.HTTP_404_NOT_FOUND)

class DidNotReceiveInputFilesException(TriplexException):
    def __str__(self):
        return "Did not receive expected input files"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="Did not receive expected input files",
            errorCode= status.HTTP_400_BAD_REQUEST)

class TokenIsNotStateSubmittedException(TriplexException):
    def __str__(self):
        return "The requested token is in the system but not in state Submitted; cannot accept incoming data"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="The requested token is in the system but not in state Submitted; cannot accept incoming data")
            
class DataNotReadyYetException(TriplexException):
    def __str__(self):
        return "Job is not completed yet"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="Job is not completed yet",
            errorCode= status.HTTP_307_TEMPORARY_REDIRECT)
class DataExpiredException(TriplexException):
    def __str__(self):
        return "Job data expired and is not available anymore"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="Job data expired and is not available anymore",
            errorCode= status.HTTP_410_GONE)
            
class JobCancelledException(TriplexException):
    def __str__(self):
        return "Job was cancelled"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="Job was cancelled",
            errorCode= status.HTTP_410_GONE)
class JobFailedException(TriplexException):
    def __str__(self):
        return "Job failed"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="Job failed",
            errorCode= status.HTTP_410_GONE)

class TriplexParamOutOfBound(TriplexException):
    def __init__(self, message):
        self.message = message 
        super().__init__()

    def __str__(self):
        try:
            return f"Triplex parameter out of bounds: {self.message}"
        except Exception:
            return "Triplex parameter out of bounds"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message=self.message,
            errorCode= status.HTTP_400_BAD_REQUEST)

class Unauthorized(TriplexException):
    def __str__(self):
        return "Qualcuno sta provando a fare il furbetto??"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="Qualcuno sta provando a fare il furbetto??",
            errorCode= status.HTTP_401_UNAUTHORIZED)

class InputFileTooBig(TriplexException):
    def __init__(self, message):
        self.message = message 
        super().__init__()

    def __str__(self):
        try:
            return f"Input file too big: {self.message}"
        except Exception:
            return "Input file too big"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message=self.message,
            errorCode= status.HTTP_400_BAD_REQUEST)

class TPXNotFound(TriplexException):
    def __str__(self):
        return "No tpx found"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="No tpx found",
            errorCode= status.HTTP_404_NOT_FOUND)

class BackgroundGenesNotIncludedInPutative(TriplexException):
    def __str__(self):
        return "Background genes are not included in putative genes"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="Background genes are not included in putative genes",
            errorCode= status.HTTP_400_BAD_REQUEST)

class BackgroundGenesNotIncludedInMANE(TriplexException):
    def __init__(self, genes):
        self.genes = genes 
        super().__init__()

    def __str__(self):
        try:
            return f"Background genes not included in MANE: {self.genes}"
        except Exception:
            return "Background genes not included in MANE"

    def handle(self): #notIncludedInMANE
        print_error(self)
        return Responses.personalized_failure(
            {"notIncludedInMANE": self.genes},
            errorCode= status.HTTP_400_BAD_REQUEST)

class JobNotStandardException(TriplexException):
    def __str__(self):
        return "This type of job does not support the requested operation"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="This type of job does not support the requested operation",
            errorCode= status.HTTP_400_BAD_REQUEST)
class HashDoesNotBatchException(TriplexException):
    def __str__(self):
        return "The tarball uploaded is not the one generated during export"

    def handle(self):
        print_error(self)
        return Responses.generic_failure(
            message="The tarball uploaded is not the one generated during export",
            errorCode= status.HTTP_401_UNAUTHORIZED)
