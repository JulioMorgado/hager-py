# AUTOGENERATED! DO NOT EDIT! File to edit: 00_hagerstrand.ipynb (unless otherwise specified).

__all__ = ['Diffusion', 'SimpleDiffusion', 'AdvancedDiffusion']

# Cell
import sys
from random import randint
from random import uniform
import numpy as np
from scipy.spatial.distance import cdist
from skimage import data, io, filters
sys.setrecursionlimit(11500)

# Cell
class Diffusion(object):
    """General class for all types of diffusion"""
    #por lo pronto solo la creación del espacio se deriva a las clases hijas?
    def __init__(self,mif_size=5,pob=20,initial_diff=[(50,50)],
                p0=0.3, max_iter=15):
        self._pob = pob
        self._p0 = p0
        self.max_iter = max_iter
        self.mif_size = mif_size
        self.iteration = 0
        self._infected_pop = []
        self._tmp_adopted = []
        self._clean = False
        self._initial_diff = initial_diff
        self.time_series = []
        self.mif_size = mif_size

    def initialize_mif(self,mif_size):
        """Initialize the MIF"""
        x = np.linspace(0.5,mif_size - 0.5,mif_size)
        y = np.linspace(0.5,mif_size - 0.5,mif_size)
        xv,yv = np.meshgrid(x,y)
        points = np.array(list(zip(np.ravel(xv),np.ravel(yv))))
        center = np.array([[mif_size/2 + 0.5,mif_size/2 + 0.5]])
        #print(points)
        #print(center)
        dist = cdist(center,points)
        dist = dist/np.sum(dist)
        #Everything: has to be different to respect the user's p0
        # print(type(mif_size), type(mif_size/2), mif_size/2)
        dist.reshape(mif_size, mif_size)[int(mif_size/2 + 0.5), int(mif_size/2 + 0.5)] = self._p0
        dist = dist/np.sum(dist)
        return np.cumsum(dist)


    def _mif2delta(self,index):
        """Returns a tuple with the increments to get to the propagated frame."""

        return np.unravel_index(index,(self.mif_size,self.mif_size))

    def _select_from_mif(self):
        """Returns an address (pob_adress) from the MIF."""
        rnd = uniform(0,1)
        index = np.nonzero(self._mif>rnd)[0][0]
        return self._mif2delta(index)

    def _clean_adopters(self):
        """Clean and initialize before a new simulation."""

        self._infected_pop = []
        self._tmp_adopted = []
        self._pop_array = np.zeros((len(np.ravel(self.space)),self._pob),
                                    dtype=np.bool)
        self.time_series = []
        for c in self._initial_diff:
            self.space[c[0],c[1]] = 1
            #We also modify the original settlers:
            index = self._space2pop_index(c)
            self._pop_array[index][0] = True
            self._infected_pop.append((index,0))

        self._clean = False

# Cell
class SimpleDiffusion(Diffusion):
    """Simple model of spatial diffusion based on Hägerstrand.
    1.- Homogeneous and isotropic space
    2.- A single initial diffuser
    3.- ....other assumptions...
    :param N: int Number of rows in simulation space.
    :param M: int Number of columns in simulation space.
    :param mif_size: int MIF matrix (square) size (must be non).
    :param pob: int population in each cell.
    :param initial_diff: [(int,int)] Coordinate list of start diffusers.
    :param p0: float Probability of self-diffusion.
    :param max_iter: int Maximum number of iterations.
    :attribute space: np.array(M,N,dtype=np.int8) Available space.
    :attribute _pop_array: np.array(M*N,pob,dtype=np.bool) array of population in each cell
    :attribute _infected_pop: list (space_idx,int) List of the adopting cell indices.
                                                The first entry is the flattened index of the cell
                                                in the space array and the second is the number of
                                                the settler in pop_array. That is, the list of addresses
                                                of each infected resident.
    :attribute results: np.array((M,N,max_iter)) Save the results of each iteration.
    :attribute time_series: list int Propagations for each iteration.
    :attribute _clean: bool Indicates if we have saved results.
    """

    def __init__(self,N=100,M=100,mif_size=5,pob=20,initial_diff=[(50,50)],
                p0=0.3, max_iter=15):

        super().__init__(mif_size, pob, initial_diff, p0, max_iter)
        # super(SimpleDiffusion,self).__init__(mif_size,pob,initial_diff,
        #             p0, max_iter)
        self.M = M
        self.N = N
        self.space = np.zeros((self.N,self.M),dtype=np.int8)
        self._pop_array = np.zeros((len(np.ravel(self.space)),pob),
                                    dtype=np.bool)
        self.result = np.zeros((M,N,max_iter),dtype=np.int8)
        for c in initial_diff:
            if c[0] > M or c[1] > N:
                raise ValueError("The coordinates on the starting difusors do not belong to the space")
            #Modificamos también a los pobladores originales:
            index = self._space2pop_index(c)
            self._pop_array[index][0] = True
            self._infected_pop.append((index,0))
        if self.mif_size%2 == 0:
            raise ValueError("MIF size must be non")
        else:
            self._mif = self.initialize_mif(self.mif_size)

    def initialize_mif(self,mif_size):
        return super(SimpleDiffusion,self).initialize_mif(self.mif_size)

    def _propagate(self,pob_adress):
        """It propagates towards the inhabitant in pob_adress if it is non-adopter.
        :param pob_adress: (int,int) the address of the inhabitant to propagate.
                           The first entry is the index (flattened) in space and
                           the second is the number of the settler in the cell
        """

        #checo si es no-adoptante
        if self._pop_array[pob_adress[0]][pob_adress[1]] == False:
            self._pop_array[pob_adress[0]][pob_adress[1]] = True
            self._tmp_adopted.append(pob_adress)
            #print "infecté al "  + str(pob_adress)

        else:
            pass


    def _space2pop_index(self,index):
        """Transform the index of space into the index of the pop_array.
        :param index (int,int) the index to transform
        """
        # print(type(index), index)
        return np.ravel_multi_index(index,dims=(self.M,self.N))

    def _pop2space_index(self,index):
        """Return the tuple (i,j)  that corresponds to the flattened index."""
        return np.unravel_index(index, (self.M,self.N))

    def _mif2delta(self,index):
        """Returns a tuple with the increments to get to the propagated frame."""
        return super(SimpleDiffusion,self)._mif2delta(index)

    def _random_adress(self):
        """Returns a random address (pob_adress)."""
        return (randint(0,(self.M*self.N) - 1),randint(0,self._pob - 1))

    def _select_from_mif(self):
        """Returns an address (pob_adress) from the MIF."""
        return super(SimpleDiffusion,self)._select_from_mif()

    def _get_propagation_adress(self,adress):
        """Returns a pop_adress address propagated by the MIF"""

        #print "Propagó: " + str(adress)
        delta = self._select_from_mif()
        delta = (delta[0] - int(self.mif_size/2+0.5),delta[1] - int(self.mif_size/2+0.5))
        space_adress = self._pop2space_index(adress[0])
        prop_space_adress = (space_adress[0] + delta[0],
                              space_adress[1] + delta[1])
        try:
            habitant = randint(0,self._pob - 1)
            return (self._space2pop_index(prop_space_adress),habitant)
        except ValueError:
            return self._get_propagation_adress(adress)

    def _clean_adopters(self):
        """Clean and initialize before a new simulation."""
        return super(SimpleDiffusion,self)._clean_adopters()

    def spatial_diffusion(self):
        """Propagate the Hagerstrand way."""

        #If we already have results, we must clean and initialize
        if self._clean:
            self._clean_adopters()

        if self.iteration == (self.max_iter or
                              np.sum(self._pop_array) >= self.M*self.N*self._pob):
            print("finished")
            print("There are %i adopters out of a total of %i inhabitants" \
                    % (np.sum(self._pop_array),self.M*self.N*self._pob))
            print("The total number of iterations performed is: %i" % self.iteration)
            self.iteration = 0
            self._clean = True
            return None
        else:
            for adress in self._infected_pop:
                propagated_adress = self._get_propagation_adress(adress)
                self._propagate(propagated_adress)

            self._infected_pop.extend(self._tmp_adopted)
            #print "Hay %i adoptantes" % len(self._infected_pop)
            self.result[:,:,self.iteration] = np.sum(self._pop_array,
                                                axis=1).reshape(self.M,self.N)
            self.time_series.append(len(self._tmp_adopted))
            self.iteration += 1
            self._tmp_adopted = []
            return self.spatial_diffusion()

    def random_diffusion(self):
        """Randomly propagates in space."""

        #If we already have results, we must clean and initialize
        if self._clean:
            self._clean_adopters()

        if self.iteration == (self.max_iter or
                              np.sum(self._pop_array) >= self.M*self.N*self._pob):
            #self.space = np.sum(s._pop_array,axis=1).reshape(s.M,s.N)
            print("finished")
            print("There are %i adopters out of a total of %i inhabitants" \
                    % (np.sum(self._pop_array),self.M*self.N*self._pob))
            print("The total number of iterations performed is: %i" % self.iteration)
            self.iteration = 0
            self._clean = True
            return None
        else:
            for adress in self._infected_pop:
                rand_adress = self._random_adress()
                if adress == rand_adress:
                    #TODO: you have to change, it could happen to get twice the same
                    rand_adress = self._random_adress()

                self._propagate(rand_adress)

            self._infected_pop.extend(self._tmp_adopted)
            #print "Hay %i adoptantes" % len(self._infected_pop)
            self.result[:,:,self.iteration] = np.sum(self._pop_array,
                                                axis=1).reshape(self.M,self.N)
            self.time_series.append(len(self._tmp_adopted))
            self.iteration += 1
            self._tmp_adopted = []
            return self.random_diffusion()

    def mixed_diffusion(self,proportion=0.5):
        """ Mix the two types of diffusion.
            In each iteration he randomly chooses, according to proportion, the
            points that diffuse randomly and those that do so spatially.
             :param proportion: float Proportion of adopters who diffuse spatially.
        """

        if proportion < 0 or proportion > 1:
            raise ValueError("The proportion must be between 0 and 1.")

        #If we already have results, we must clean and initialize
        if self._clean:
            self._clean_adopters()

        if self.iteration == (self.max_iter or
                              np.sum(self._pop_array) >= self.M*self.N*self._pob):
            #self.space = np.sum(s._pop_array,axis=1).reshape(s.M,s.N)
            print("finished")
            print("There are %i adopters out of a total of %i inhabitants" \
                    % (np.sum(self._pop_array),self.M*self.N*self._pob))
            print("The total number of iterations performed is: %i" % self.iteration)
            self.iteration = 0
            self._clean = True
            return None
        else:
            for adress in self._infected_pop:
                rnd = uniform(0,1)
                if rnd <= proportion:
                    propagated_adress = self._get_propagation_adress(adress)
                    self._propagate(propagated_adress)
                else:
                    rand_adress = self._random_adress()
                    if adress == rand_adress:
                        #TODO: you have to change, it could happen to get twice the same
                        rand_adress = self._random_adress()

                    self._propagate(rand_adress)

            self._infected_pop.extend(self._tmp_adopted)
            #print "There are %i adopters %i len(self._infected_pop)
            self.result[:,:,self.iteration] = np.sum(self._pop_array,
                                                axis=1).reshape(self.M,self.N)
            self.time_series.append(len(self._tmp_adopted))
            self.iteration += 1
            self._tmp_adopted = []
            return self.mixed_diffusion(proportion)

# Cell
class AdvancedDiffusion(Diffusion):
    """Modelo de difusión espacial basado en Hägerstrand, con espacio heterogéneo.
    1.- Espacio isotrópico
    2.- Un sólo difusor inicial
    3.- ....otras suposiciones...
    :param N: int Número de renglones y columnas en el espacio de simulación
    :param mif_size: int Tamaño de la matriz (cuadrada) del MIF (debe ser non)
    :param pob: int población máxima en cada celda
    :param densidad: int Cantidad de núcleos iniciales de población.
    :param amplitud: float Amplitud del filtro gaussiano para difuminar la población.
    :param initial_diff: [(int,int)] Lista de coordenadas de los difusores
                                     iniciales
    :param p0: float Probabilidad de auto-difusión
    :param max_iter: int Máximo número de iteraciones
    :attribute space: np.array(N,N,dtype=np.int8) El espacio disponible
    :attribute _pop_array: np.array(N*N,pob,dtype=np.bool) array de habitantes
                           en cada celda
    :attribute _infected_pop: list (space_idx,int) Lista de los índices de las
                                celdas adoptantes. La primera entrada es el
                                índice aplanado de la celda en la matriz space y
                                la segunda es el número del poblador en
                                pop_array. Es decir, la lista de las direcciones
                                de cada poblador infectado.
    :attribute results: np.array((N,N,max_iter)) Guarda los resultados de cada
                        iteración.
    :attribute time_series: list int Propagaciones por cada iteración
    :attribute _clean: bool Indica si tenemos resultados guardados .
    """

    def __init__(self,N=100,mif_size=5,pob=20,initial_diff=[(50,50)],
                p0=0.3, max_iter=25,densidad=20,amplitud=4.0):
        super(AdvancedDiffusion,self).__init__(mif_size,pob,initial_diff, p0,
                                                max_iter)
        self.N = N
        self.densidad = densidad
        self.amplitud = amplitud
        self.space = np.zeros((self.N,self.N),dtype=np.int8)
        points = self.N * np.random.random((2, self.densidad ** 2))
        self.space[(points[0]).astype(np.int), (points[1]).astype(np.int)] = 1
        self.space = filters.gaussian(self.space, sigma= self.N / (self.amplitud * self.densidad))
        #reescalamos al valor de la pob máxima y convertimos a entero:
        self.space *= self._pob / self.space.max()
        self.space = self.space.astype(np.int8)
        self._pop_array = np.zeros((len(np.ravel(self.space)),self._pob),
                                    dtype=np.bool)
        self.result = np.zeros((self.N,self.N,max_iter),dtype=np.int8)
        for c in initial_diff:
            if c[0] > self.N or c[1] > self.N:
                raise ValueError("Las coordenadas de los difusores iniciales no \
                                caen en el espacio")
            #Modificamos también a los pobladores originales:
            index = self._space2pop_index(c)
            self._pop_array[index][0] = True
            self._infected_pop.append((index,0))

        if self.mif_size%2 == 0:
            raise ValueError("El tamaño del MIF debe ser non")
        else:
            self._mif = self.initialize_mif(self.mif_size)

    def _space2pop_index(self,index):
        """Transforma el índice de space en el índice del pop_array.
        :param index (int,int) el ínidice a transformar
        """
        return np.ravel_multi_index(index,dims=(self.N,self.N))

    def _pop2space_index(self,index):
        """Regresa la tupla (i,j) que corresponde al índice aplanado."""
        return np.unravel_index(index,(self.N,self.N))

    def _mif2delta(self,index):
        """Regresa un tupla con los incrementos para llegar al cuadro propagado."""
        return super(AdvancedDiffusion,self)._mif2delta(index)

    def _select_from_mif(self):
        """Regresa una dirección (pob_adress) a partir del MIF."""
        return super(AdvancedDiffusion,self)._select_from_mif()

    def _random_adress(self):
        """Regresa una dirección (pob_adress) al azar."""
        i = randint(0,self.N - 1)
        j = randint(0,self.N - 1)
        pop_idx = self._space2pop_index((i,j))
        #space_idx = self._pop2space_index(i*j)
        return (pop_idx,randint(0,self.space[i,j] - 1))

    def _get_propagation_adress(self,adress):
        """Regresa una dirección pop_adress propagada por el MIF"""

        #print "Propagó: " + str(adress)
        delta = self._select_from_mif()
        delta = (delta[0] - int(self.mif_size/2+0.5),delta[1] - int(self.mif_size/2+0.5))
        space_adress = self._pop2space_index(adress[0])
        prop_space_adress = (space_adress[0] + delta[0],
                             space_adress[1] + delta[1])
        try:
            # print(prop_space_adress[0],prop_space_adress[1])
            # print(self.space[prop_space_adress[0],prop_space_adress[1]])
            habitant = randint(0,self.space[prop_space_adress[0],prop_space_adress[1]])
            return (self._space2pop_index(prop_space_adress),habitant)
        except ValueError as e:
            return self._get_propagation_adress(adress)

    def _propagate(self,pob_adress):
        """Propaga hacia el habitante en pob_adress si es no-adoptante.
        :param pob_adress: (int,int) la dirección del habitante a propagar.
                            La primera entrada es el índice (aplanado) en space
                            y la segunda es el número del poblador en la celda
        """

        #checo si es no-adoptante
        try:
            if self._pop_array[pob_adress[0]][pob_adress[1]] == False:
                self._pop_array[pob_adress[0]][pob_adress[1]] = True
                self._tmp_adopted.append(pob_adress)
            else:
                pass
        except IndexError:
            # This means we are infecting someone outside the space
            pass

    def _clean_adopters(self):
        """Limpia e inicializa antes de una nueva simulación."""
        return super(AdvancedDiffusion,self)._clean_adopters()

    def spatial_diffusion(self):
        """Propaga al estilo Hagerstrand."""

        #Si ya tenemos resultados hay que limpiar e inicializar
        if self._clean:
            self._clean_adopters()

        if self.iteration == (self.max_iter or
                              np.sum(self._pop_array) >= self.M*self.N*self._pob):
            print("acabé")
            print("Hay %i adoptantes de un total de %i habitantes" \
                    % (np.sum(self._pop_array),self.N * self.N * self._pob))
            print("El total de iteraciones realizadas es %i" % self.iteration)
            self.iteration = 0
            self._clean = True
            return None
        else:
            for adress in self._infected_pop:
                propagated_adress = self._get_propagation_adress(adress)
                self._propagate(propagated_adress)

            self._infected_pop.extend(self._tmp_adopted)
            #print "Hay %i adoptantes" % len(self._infected_pop)
            self.result[:,:,self.iteration] = np.sum(self._pop_array,
                                                axis=1).reshape(self.N,self.N)
            self.time_series.append(len(self._tmp_adopted))
            self.iteration += 1
            self._tmp_adopted = []
            return self.spatial_diffusion()

    def random_diffusion(self):
        """Propaga aleatoriamente en el espacio."""

        #Si ya tenemos resultados hay que limpiar e inicializar
        if self._clean:
            self._clean_adopters()

        if self.iteration == (self.max_iter or
                              np.sum(self._pop_array) >= self.N*self.N*self._pob):
            #self.space = np.sum(s._pop_array,axis=1).reshape(s.M,s.N)
            print("acabé")
            print("Hay %i adoptantes de un total de %i habitantes" \
                    % (np.sum(self._pop_array),self.N*self.N*self._pob))
            print("El total de iteraciones realizadas es %i" % self.iteration)
            self.iteration = 0
            self._clean = True
            return None
        else:
            for adress in self._infected_pop:
                rand_adress = self._random_adress()
                if adress == rand_adress:
                    #TODO: hay que cambiar, podría pasar obtener dos veces
                    #el mismo
                    rand_adress = self._random_adress()

                self._propagate(rand_adress)

            self._infected_pop.extend(self._tmp_adopted)
            #print "Hay %i adoptantes" % len(self._infected_pop)
            self.result[:,:,self.iteration] = np.sum(self._pop_array,
                                                axis=1).reshape(self.N,self.N)
            self.time_series.append(len(self._tmp_adopted))
            self.iteration += 1
            self._tmp_adopted = []
            return self.random_diffusion()