# coding: utf-8
# Standard Python libraries
import io
from typing import Optional, Tuple, Union
from pathlib import Path
import datetime

# https://numpy.org/
import numpy as np
import numpy.typing as npt

# https://github.com/usnistgov/DataModelDict
from DataModelDict import DataModelDict as DM

# https://github.com/usnistgov/yabadaba
from yabadaba import query

# local imports
from ..tools import atomic_mass, aslist
from .BasePotentialLAMMPS import BasePotentialLAMMPS
from .Artifact import Artifact

class PotentialLAMMPS(BasePotentialLAMMPS):
    """
    Class for building LAMMPS input lines from a potential-LAMMPS data model.
    """
    
    def __init__(self,
                 model: Union[str, io.IOBase, DM, None] = None,
                 name: Optional[str] = None,
                 pot_dir: Optional[str] = None):
        """
        Initializes an instance and loads content from a data model.
        
        Parameters
        ----------
        model : str, file-like object or DataModelDict, optional
            A JSON/XML data model for the content.
        name : str, optional
            The record name to use.  If not given, this will be set to the
            potential's id.
        pot_dir : str, optional
            The path to a directory containing any artifacts associated with
            the potential.  Default value is None, which assumes any required
            files will be in the working directory when LAMMPS is executed.
        """
        super().__init__(model=model, name=name, pot_dir=pot_dir)
        if model is None and pot_dir is not None:
            self.pot_dir = pot_dir

    @property
    def style(self) -> str:
        """str: The record style"""
        return 'potential_LAMMPS'

    @property
    def modelroot(self) -> str:
        """str : The root element for the associated data model"""
        return 'potential-LAMMPS'

    @property
    def xsl_filename(self) -> Tuple[str, str]:
        """tuple: The module path and file name of the record's xsl html transformer"""
        return ('potentials.xsl', 'potential_LAMMPS.xsl')

    @property
    def xsd_filename(self) -> Tuple[str, str]:
        """tuple: The module path and file name of the record's xsd schema"""
        return ('potentials.xsd', 'potential_LAMMPS.xsd')

    @property
    def fileurls(self) -> list:
        """list : The URLs where the associated files can be downloaded"""
        urls = []
        for artifact in self.artifacts:
            urls.append(artifact.url)
        return urls
    
    @property
    def dois(self) -> list:
        """list : The publication DOIs associated with the potential"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__dois

    @property
    def comments(self) -> str:
        """str : Descriptive comments detailing the potential information"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__comments

    @property
    def print_comments(self) -> str:
        """str : LAMMPS print commands of the potential comments"""

        # Split defined comments
        lines = self.comments.split('\n')

        out = ''
        for line in lines:
            if line != '':
                out += f'print "{line}"\n'
        
        if len(self.dois) > 0:
            out += 'print "Publication(s) related to the potential:"\n'
            for doi in self.dois:
                out += f'print "https://doi.org/{doi}"\n'

        if len(self.fileurls) > 0:
            out += 'print "Parameter file(s) can be downloaded at:"\n'

            for url in self.fileurls:
                out += f'print "{url}"\n'
        return out
 
    @property
    def artifacts(self) -> list:
        """list : The list of file artifacts for the potential including download URLs."""
        return self.__artifacts

    def load_model(self, model, name=None, pot_dir=None):
        """
        Loads potential-LAMMPS data model info.
        
        Parameters
        ----------
        model : str, file-like object or DataModelDict
            A JSON/XML data model for the content.
        name : str, optional
            The name to assign to the record.  Often inferred from other
            attributes if not given.
        pot_dir : str, optional
            The path to a directory containing any artifacts associated with
            the potential.  Default value is None, which assumes any required
            files will be in the working directory when LAMMPS is executed.
        """
        # Call parent load to read model and some parameters
        super().load_model(model, name=name)
        pot = self.model[self.modelroot]
        
        if pot_dir is not None:
            self.pot_dir = pot_dir
        else:
            self.pot_dir = ''
        
        # Add artifacts
        self.__artifacts = []
        for artifact in pot.aslist('artifact'):
            self.__artifacts.append(Artifact(model=DM([('artifact', artifact)])))

        # Read comments, if present
        self.__comments = pot.get('comments', '')
        self.__dois = pot['potential'].aslist('doi')
        
        # Build lists of symbols, elements and masses
        self._elements = []
        self._symbols = []
        self._masses = []
        self._charges = []
        for atom in pot.iteraslist('atom'):
            element = atom.get('element', None)
            symbol = atom.get('symbol', None)
            mass = atom.get('mass', None)
            charge = float(atom.get('charge', 0.0))
            
            # Check if element is listed
            if element is None:
                if mass is None:
                    raise KeyError('mass is required for each atom if element is not listed')
                if symbol is None:
                    raise KeyError('symbol is required for each atom if element is not listed')
                else:
                    element = symbol
            
            # Check if symbol is listed.
            if symbol is None:
                symbol = element
            
            # Add values to the lists
            self._elements.append(element)
            self._symbols.append(symbol)
            self._masses.append(mass)
            self._charges.append(charge)
    
    def mongoquery(self,
                   name: Union[str, list, None] = None,
                   key: Union[str, list, None] = None,
                   id: Union[str, list, None] = None,
                   potid: Union[str, list, None] = None,
                   potkey: Union[str, list, None] = None,
                   units: Union[str, list, None] = None,
                   atom_style: Union[str, list, None] = None,
                   pair_style: Union[str, list, None] = None,
                   status: Union[str, list, None] = None,
                   symbols: Union[str, list, None] = None,
                   elements: Union[str, list, None] = None) -> dict:
        """
        Builds a Mongo-style query based on kwargs values for the record style.
        
        Parameters
        ----------
        name : str or list, optional
            The record name(s) to parse by.
        key : str or list, optional
            The UUID4 key(s) associated with the LAMMPS implementations to
            parse by.
        id : str or list, optional
            The unique id(s) associated with the LAMMPS implementations to
            parse by.
        potid : str or list, optional
            The unique id(s) associated with the general potential model to
            parse by.
        potkey : str or list, optional
            The UUID4 key(s) associated with the general potential model to
            parse by.
        units : str or list, optional
            The LAMMPS unit style(s) to parse by.
        atom_style : str or list, optional
            The LAMMPS atom_style values(s) to parse by.
        pair_style : str or list, optional
            The LAMMPS pair_style values(s) to parse by.
        status : str or list, optional
            The implementation status value(s) to parse by.
        symbols : str or list, optional
            Symbol model(s) to parse by.
        elements : str or list, optional
            Elemental tag(s) to parse by.
        
        Returns
        -------
        dict
            The Mongo-style query
        """
        if status is not None:
            status = aslist(status)
            if 'active' in status:
                status.append(None)

        mquery = {}
        query.str_match.mongo(mquery, f'name', name)

        root = f'content.{self.modelroot}'
        query.str_match.mongo(mquery, f'{root}.key', key)
        query.str_match.mongo(mquery, f'{root}.id', id)
        query.str_match.mongo(mquery, f'{root}.potential.id', potid)
        query.str_match.mongo(mquery, f'{root}.potential.key', potkey)
        query.str_match.mongo(mquery, f'{root}.units', units)
        query.str_match.mongo(mquery, f'{root}.atom_style', atom_style)
        query.str_match.mongo(mquery, f'{root}.pair_style.type', pair_style)
        query.str_match.mongo(mquery, f'{root}.status', status)
        query.in_list.mongo(mquery, f'{root}.atom.element', elements)
        query.in_list.mongo(mquery, f'{root}.atom.symbol', symbols)

        return mquery

    def cdcsquery(self,
                  key: Union[str, list, None] = None,
                  id: Union[str, list, None] = None,
                  potid: Union[str, list, None] = None,
                  potkey: Union[str, list, None] = None,
                  units: Union[str, list, None] = None,
                  atom_style: Union[str, list, None] = None,
                  pair_style: Union[str, list, None] = None,
                  status: Union[str, list, None] = None,
                  symbols: Union[str, list, None] = None,
                  elements: Union[str, list, None] = None) -> dict:
        """
        Builds a CDCS-style query based on kwargs values for the record style.
        
        Parameters
        ----------
        key : str or list, optional
            The UUID4 key(s) associated with the LAMMPS implementations to
            parse by.
        id : str or list, optional
            The unique id(s) associated with the LAMMPS implementations to
            parse by.
        potid : str or list, optional
            The unique id(s) associated with the general potential model to
            parse by.
        potkey : str or list, optional
            The UUID4 key(s) associated with the general potential model to
            parse by.
        units : str or list, optional
            The LAMMPS unit style(s) to parse by.
        atom_style : str or list, optional
            The LAMMPS atom_style values(s) to parse by.
        pair_style : str or list, optional
            The LAMMPS pair_style values(s) to parse by.
        status : str or list, optional
            The implementation status value(s) to parse by.
        symbols : str or list, optional
            Symbol model(s) to parse by.
        elements : str or list, optional
            Elemental tag(s) to parse by.
        
        Returns
        -------
        dict
            The CDCS-style query
        """
        if status is not None:
            status = aslist(status)
            if 'active' in status:
                status.append(None)

        mquery = {}
        root = self.modelroot

        query.str_match.mongo(mquery, f'{root}.key', key)
        query.str_match.mongo(mquery, f'{root}.id', id)
        query.str_match.mongo(mquery, f'{root}.potential.id', potid)
        query.str_match.mongo(mquery, f'{root}.potential.key', potkey)
        query.str_match.mongo(mquery, f'{root}.units', units)
        query.str_match.mongo(mquery, f'{root}.atom_style', atom_style)
        query.str_match.mongo(mquery, f'{root}.pair_style.type', pair_style)
        query.str_match.mongo(mquery, f'{root}.status', status)
        query.in_list.mongo(mquery, f'{root}.atom.element', elements)
        query.in_list.mongo(mquery, f'{root}.atom.symbol', symbols)

        return mquery
    
    @property
    def symbolsets(self) -> list:
        """list : The sets of symbols that correspond to all related potentials"""
        return [self._symbols]

    def metadata(self) -> dict:
        """Returns a flat dict of the metadata fields"""
        
        d = super().metadata()
        d['artifacts'] = []
        for artifact in self.artifacts:
            d['artifacts'].append(artifact.metadata())
        d['comments'] = self.comments
        d['dois'] = self.dois

        return d

    def pair_info(self,
                  symbols: Union[str, list, None] = None,
                  masses: Union[float, list, None] = None,
                  units: Optional[str] = None,
                  prompt: bool = False,
                  comments: bool = True,
                  lammpsdate: datetime.date = datetime.date(2020, 10, 29)
                  ) -> str:
        """
        Generates the LAMMPS input command lines associated with the Potential
        and a list of atom-model symbols.
        
        Parameters
        ----------
        symbols : str or list, optional
            List of atom-model symbols corresponding to the atom types in a
            system.  If None (default), then all atom-model symbols will
            be included in the order that they are listed in the data model.
        masses : float or list, optional
            Can be given to override the default symbol-based masses for each
            atom type.  Must be a list of the same length as symbols.  Any
            values of None in the list indicate that the default value be used
            for that atom type.
        units : str, optional
            The LAMMPS unit setting to use for the output.  If not given,
            will use the default value set for the potential.
        prompt : bool, optional
            If True, then a screen prompt will appear for radioactive elements
            with no standard mass to ask for the isotope to use. If False
            (default), then the most stable isotope will be automatically used.
        comments : bool, optional
            Indicates if print command lines detailing information on the potential
            are to be included.  Default value is True.
        lammpsdate : datetime, optional
            The LAMMPS version date that is to be used.  The generated commands
            may differ based on the version of LAMMPS used.

        Returns
        -------
        str
            The LAMMPS input command lines that specifies the potential.
        """

        # Use all symbols if symbols is None
        if symbols is None:
            symbols = self.symbols
        else:
            symbols = aslist(symbols)

        # Check length of given masses
        if masses is not None:
            masses = aslist(masses)
            assert len(masses) == len(symbols), 'supplied masses must be same length as symbols'
        else:
            masses = [None,]

        # Normalize symbols and masses
        symbols = self.normalize_symbols(symbols)
        for i in range(len(masses), len(symbols)):
            masses += [None,]
        
        # Change None mass values to default values
        for i in range(len(masses)):
            if masses[i] is None:
                masses[i] = self.masses(symbols[i], prompt=prompt)[0]

        info = ''
        
        # Add comment prints
        if comments:
            info += self.print_comments

        # Generate pair_style line
        terms = self.model[self.modelroot]['pair_style'].aslist('term')
        style_terms = self.__pair_terms(terms)
        
        info += f'pair_style {self.pair_style}{style_terms}\n'
        
        # Generate pair_coeff lines
        for coeff_line in self.model[self.modelroot].iteraslist('pair_coeff'):
            if 'interaction' in coeff_line:
                interaction = coeff_line['interaction'].get('symbol', ['*', '*'])
            else:
                interaction = ['*', '*']
            
            # Always include coeff lines that act on all atoms in the system
            if interaction == ['*', '*']:
                coeff_symbols = self.symbols
                coeff_terms = self.__pair_terms(coeff_line.iteraslist('term'),
                                                symbols, coeff_symbols)
                
                info += f'pair_coeff * *{coeff_terms}\n'
                continue
            
            # Many-body potentials will contain a symbols term
            if len(coeff_line.finds('symbols')) > 0:
                many = True
            else:
                many = False
            
            # Treat as a many-body potential
            if many:
                coeff_symbols = interaction
                coeff_terms = self.__pair_terms(coeff_line.iteraslist('term'),
                                           symbols, coeff_symbols) + '\n'
                
                info += f'pair_coeff * *{coeff_terms}\n' 
            
            # Treat as pair potential
            else:
                coeff_symbols = interaction
                if len(coeff_symbols) != 2:
                    raise ValueError('Pair potential interactions need two listed elements')
                
                # Classic eam style is a special case
                if self.pair_style == 'eam':
                    if coeff_symbols[0] != coeff_symbols[1]:
                        raise ValueError('Only i==j interactions allowed for eam style')
                    for i in range(len(symbols)):
                        if symbols[i] == coeff_symbols[0]:
                            coeff_terms = self.__pair_terms(coeff_line.iteraslist('term'),
                                                           symbols, coeff_symbols)
                            
                            info += f'pair_coeff {i+1} {i+1}{coeff_terms}\n'
                
                # All other pair potentials
                else:
                    for i in range(len(symbols)):
                        for j in range(i, len(symbols)):
                            if ((symbols[i] == coeff_symbols[0] and symbols[j] == coeff_symbols[1])
                             or (symbols[i] == coeff_symbols[1] and symbols[j] == coeff_symbols[0])):
                                coeff_terms = self.__pair_terms(coeff_line.iteraslist('term'),
                                                                symbols, coeff_symbols)
                                
                                info += f'pair_coeff {i+1} {j+1}{coeff_terms}\n'
        # Generate mass lines
        for i in range(len(masses)):
            info += f'mass {i+1} {masses[i]}\n'
        info +='\n'

        # Generate additional command lines
        for command_line in self.model[self.modelroot].iteraslist('command'):
            info += self.__pair_terms(command_line.iteraslist('term'),
                                         symbols, self.symbols).strip() + '\n'
        
        return info
    
    def __pair_terms(self,
                     terms: list,
                     system_symbols: Optional[list] = None,
                     coeff_symbols: Optional[list ] = None) -> str:
        """utility function used by self.pair_info() for composing lines from terms"""
        if system_symbols is None:
            system_symbols = []
        if coeff_symbols is None:
            coeff_symbols = []
        
        line = ''
        
        for term in terms:
            for ttype, tval in term.items():
                
                # Print options and parameters as strings
                if ttype == 'option' or ttype == 'parameter':
                    line += ' ' + str(tval)
                
                # Print files with pot_dir prefixes
                elif ttype == 'file':
                    line += ' ' + str(Path(self.pot_dir, tval))
                
                # Print all symbols being used for symbolsList
                elif ttype == 'symbolsList' and (tval is True or tval.lower() == 'true'):
                    for coeff_symbol in coeff_symbols:
                        if coeff_symbol in system_symbols:
                            line += ' ' + coeff_symbol
                
                # Print symbols being used with model in appropriate order for symbols
                elif ttype == 'symbols' and (tval is True or tval.lower() == 'true'):
                    for system_symbol in system_symbols:
                        if system_symbol in coeff_symbols:
                            line += ' ' + system_symbol
                        else:
                            line += ' NULL'
        
        return line
    
    def pair_data_info(self,
                       filename: Union[str, Path],
                       pbc: npt.ArrayLike,
                       symbols: Union[str, list, None] = None,
                       masses: Union[float, list, None] = None,
                       atom_style: Optional[str] = None,
                       units: Optional[str] = None,
                       prompt: bool = False,
                       comments: bool = True,
                       lammpsdate: datetime.date = datetime.date(2020, 10, 29)
                       ) -> str:
        """
        Generates the LAMMPS command lines associated with both a potential
        and reading an atom data file.

        Parameters
        ----------
        filename : path-like object
            The file path to the atom data file for LAMMPS to read in.
        pbc : array-like object
            The three boolean periodic boundary conditions.
        symbols : str or list, optional
            List of atom-model symbols corresponding to the atom types in a
            system.  If None (default), then all atom-model symbols will
            be included in the order that they are listed in the data model.
        masses : float or list, optional
            Can be given to override the default symbol-based masses for each
            atom type.  Must be a list of the same length as symbols.  Any
            values of None in the list indicate that the default value be used
            for that atom type.
        atom_style : str, optional
            The LAMMPS atom_style setting to use for the output.  If not given,
            will use the default value set for the potential.
        units : str, optional
            The LAMMPS unit setting to use for the output.  If not given,
            will use the default value set for the potential.
        prompt : bool, optional
            If True, then a screen prompt will appear for radioactive elements
            with no standard mass to ask for the isotope to use. If False
            (default), then the most stable isotope will be automatically used.
        comments : bool, optional
            Indicates if print command lines detailing information on the potential
            are to be included.  Default value is True.
        lammpsdate : datetime, optional
            The LAMMPS version date that is to be used.  The generated commands
            may differ based on the version of LAMMPS used.

        Returns
        -------
        str
            The LAMMPS input command lines that specifies the potential and a data
            file to read.
        """
        if units is None:
            units = self.units
        if atom_style is None:
            atom_style = self.atom_style

        # Initialize comment
        info = ''

        # Add units and atom_style values
        info += f'units {units}\n'
        info += f'atom_style {atom_style}\n\n'

        # Set boundary flags to p or m based on pbc values
        bflags = np.array(['m','m','m'])
        bflags[pbc] = 'p'
        info += f'boundary {bflags[0]} {bflags[1]} {bflags[2]}\n'
    
        # Set read_data command       
        if isinstance(filename, str):
            info += f'read_data {filename}\n'

        # Set pair_info
        info += '\n'
        info += self.pair_info(symbols=symbols, masses=masses, prompt=prompt,
                               comments=comments)

        return info

    def pair_restart_info(self,
                          filename: Union[str, Path],
                          symbols: Union[str, list, None] = None,
                          masses: Union[float, list, None] = None,
                          units: Optional[str] = None,
                          prompt: bool = False,
                          comments: bool = True,
                          lammpsdate: datetime.date = datetime.date(2020, 10, 29)
                          ) -> str:
        """
        Generates the LAMMPS command lines associated with both a potential
        and reading an atom data file.

        Parameters
        ----------
        filename : path-like object
            The file path to the restart file for LAMMPS to read in.
        symbols : str or list, optional
            List of atom-model symbols corresponding to the atom types in a
            system.  If None (default), then all atom-model symbols will
            be included in the order that they are listed in the data model.
        masses : float or list, optional
            Can be given to override the default symbol-based masses for each
            atom type.  Must be a list of the same length as symbols.  Any
            values of None in the list indicate that the default value be used
            for that atom type.
        units : str, optional
            The LAMMPS unit setting to use for the output.  If not given,
            will use the default value set for the potential.
        prompt : bool, optional
            If True, then a screen prompt will appear for radioactive elements
            with no standard mass to ask for the isotope to use. If False
            (default), then the most stable isotope will be automatically used.
        comments : bool, optional
            Indicates if print command lines detailing information on the potential
            are to be included.  Default value is True.
        lammpsdate : datetime, optional
            The LAMMPS version date that is to be used.  The generated commands
            may differ based on the version of LAMMPS used.

        Returns
        -------
        str
            The LAMMPS input command lines that specifies the potential and a restart
            file to read.
        """
        # Add comment line
        info = '# Script prepared using atomman Python package\n\n'
    
        # Set read_data command 
        info += f'read_restart {filename}\n'

        # Set pair_info
        info += '\n'
        info += self.pair_info(symbols=symbols, masses=masses, prompt=prompt,
                               comments=comments)

        return info

    
