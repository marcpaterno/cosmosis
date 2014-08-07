from .elements import PostProcessorElement
from ..plotting import cosmology_theory_plots
from ..plotting.kde import KDE
import pylab
import ConfigParser
import numpy as np
import scipy.optimize
import matplotlib
#We have quite a lot of figures open at once here
matplotlib.rcParams['figure.max_open_warning'] = 100

class Plots(PostProcessorElement):
    def __init__(self, *args, **kwargs):
        super(Plots, self).__init__(*args, **kwargs)
        self.figures = {}
        latex_file = self.options.get("latex") 
        self._latex = {}
        if latex_file:
            self.load_latex(latex_file)

    def load_latex(self, latex_file):
        latex_names = {}
        latex_names = ConfigParser.ConfigParser()
        latex_names.read(latex_file)
        for i,col_name in enumerate(self.source.colnames):
            display_name=col_name
            if '--' in col_name:
                section,name = col_name.lower().split('--')
                try:
                    display_name = latex_names.get(section,name)
                except ConfigParser.NoOptionError:
                    pass                    
            else:
                if col_name in ["LIKE","like", "likelihood"]:
                    display_name=r"{\cal L}"
            self._latex[col_name]=display_name

    def latex(self, name, dollar):
        l = self._latex.get(name, name)
        if dollar:
            l = "$"+l+"$"
        return l

    def filename(self, base):
        output_dir = self.options.get("outdir", "png")
        prefix=self.options.get("prefix","")
        ftype=self.options.get("file_type", "png")
        return "{0}/{1}{2}.{3}".format(output_dir, prefix, base, ftype)

    def figure(self, name):
        #we want to be able to plot multiple chains on the same
        #figure at some point.  So when we make figures we should
        #call this function
        fig = self.figures.get(name)
        if fig is None:
            fig = pylab.figure()
            self.figures[name] = fig
        return fig

    def save_figures(self):
        for filename, figure in self.figures.items():
            pylab.figure(figure.number)
            pylab.savefig(filename)
            pylab.close()
        self.figures = {}

    def finalize(self):
        self.save_figures()


    def run(self):
        print "I do not know how to generate plots for this kind of data"
        return []



class GridPlots1D(Plots):

    def run(self):
        return [self.plot_1d(name) for name in self.source.colnames]

    def plot_1d(self, name1):
        filename = self.filename(name1)
        cols1 = self.source.get_col(name1)
        like = self.source.get_col("like")
        vals1 = np.unique(cols1)
        n1 = len(vals1)
        like_sum = np.zeros(n1)

        #marginalize
        for k,v1 in enumerate(vals1):
            w = np.where(cols1==v1)
            like_sum[k] = np.log(np.exp(like[w]).sum())
        like = like_sum.flatten()

        #linearly interpolate
        n1 *= 10
        vals1_interp = np.linspace(vals1[0], vals1[-1], n1)
        like_interp = np.interp(vals1_interp, vals1, like)
        vals1 = vals1_interp
        like = like_interp

        #normalize
        like -= like.max()

        #Determine the spacing in the different parameters
        dx = vals1[1]-vals1[0]

        #Set up the figure
        fig = self.figure(filename)
        pylab.figure(fig.number)

        #Plot the likelihood
        pylab.plot(vals1, np.exp(like), linewidth=3)

        #Find the levels of the 68% and 95% contours
        X, L = self.find_grid_contours(like, 0.68, 0.95, vals1)
        #Plot black dotted lines from the y-axis at these contour levels
        for (x, l) in zip(X,L):
            pylab.plot([x[0],x[0]], [0, np.exp(l[0])], ':', color='black')
            pylab.plot([x[1],x[1]], [0, np.exp(l[1])], ':', color='black')

        #Set the x and y limits
        pylab.xlim(cols1.min()-dx/2., cols1.max()+dx/2.)
        pylab.ylim(0,1.05)
        #Add label
        pylab.xlabel(self.latex(name1,dollar=True))
        return filename

    @staticmethod
    def find_grid_contours(log_like, contour1, contour2, vals1, ):
        like = np.exp(log_like)
        like_total = like.sum()
        def objective(limit, target):
            w = np.where(like>limit)
            return like[w].sum() - target
        target1 = like_total*contour1
        target2 = like_total*contour2
        level1 = scipy.optimize.bisect(objective, like.min(), like.max(), args=(target1,))
        level2 = scipy.optimize.bisect(objective, like.min(), like.max(), args=(target2,))
        level1 = np.log(level1)
        level2 = np.log(level2)
        X = []
        L = []
        for level in [level1, level2]:
            above = np.where(like>level)[0]
            left = above[0]
            right = above[-1]
            x1 = vals1[left]
            x2 = vals1[right]
            L1 = like[left]
            L2 = like[right]
            X.append((x1,x2))
            L.append((L1,L2))
        return X,L

class GridPlots2D(Plots):
    pass


class MetropolisHastingsPlots(Plots):

    def keywords_1d(self):
        return {}

    def make_1d_plot(self, name):
        x = self.source.get_col(name)
        filename = self.filename(name)
        figure = self.figure(filename)

        #Interpolate using KDE
        n = self.options.get("n_kde", 100)
        factor = self.options.get("factor_kde", 2.0)
        kde = KDE(x, factor=factor)
        x_axis, like = kde.grid_evaluate(n, (x.min(), x.max()) )

        #Make the plot
        pylab.figure(figure.number)
        keywords = self.keywords_1d()
        pylab.plot(x_axis, like, '-', **keywords)
        pylab.xlabel(self.latex(name, dollar=True))

        return filename

    def run(self):
        filenames = []
        for name in self.source.colnames:
            filename = self.make_1d_plot(name)
            filenames.append(filename)
        return filenames



class MetropolisHastings2DPlots(Plots):
    def keywords_2d(self):
        return {}

    @staticmethod
    def _find_contours(like, x, y, n, xmin, xmax, ymin, ymax, contour1, contour2):
        N = len(x)
        x_axis = np.linspace(xmin, xmax, n+1)
        y_axis = np.linspace(ymin, ymax, n+1)
        histogram, _, _ = np.histogram2d(x, y, bins=[x_axis, y_axis])

        def objective(limit, target):
            w = np.where(like>limit)
            count = histogram[w]
            return count.sum() - target
        target1 = N*(1-contour1)
        target2 = N*(1-contour2)
        level1 = scipy.optimize.bisect(objective, like.min(), like.max(), args=(target1,), xtol=1./N)
        level2 = scipy.optimize.bisect(objective, like.min(), like.max(), args=(target2,), xtol=1./N)
        return level1, level2, like.sum()

    def make_2d_plot(self, name1, name2):
        #Get the data
        x = self.source.get_col(name1)
        y = self.source.get_col(name2)
        filename = self.filename("2d_"+name1+"_"+name2)
        figure = self.figure(filename)

        #Interpolate using KDE
        n = self.options.get("n_kde", 100)
        fill = self.options.get("fill", True)
        factor = self.options.get("factor_kde", 2.0)
        kde = KDE([x,y], factor=factor)
        x_range = (x.min(), x.max())
        y_range = (y.min(), y.max())
        (x_axis, y_axis), like = kde.grid_evaluate(n, [x_range, y_range])

        #Choose levels at which to plot contours
        contour1=1-0.68
        contour2=1-0.95
        level1, level2, total_mass = self._find_contours(like, x, y, n, x.min(), x.max(), y.min(), y.max(), contour1, contour2)
        level0 = 1.1
        levels = [level2, level1, level0]


        #Make the plot
        pylab.figure(figure.number)
        keywords = self.keywords_2d()
        if fill:
            pylab.contourf(x_axis, y_axis, like.T, [level2,level0], colors=['b'], alpha=0.25)
            pylab.contourf(x_axis, y_axis, like.T, [level1,level0], colors=['b'], alpha=0.25)
        else:
            pylab.contour(x_axis, y_axis, like.T, [level2,level1], colors='b')

        #Do the labels
        pylab.xlabel(self.latex(name1, dollar=True))
        pylab.ylabel(self.latex(name2, dollar=True))

        return filename        


    def run(self):
        filenames = []
        for name1 in self.source.colnames[:]:
            for name2 in self.source.colnames[:]:
                if name1==name2: continue
                filename = self.make_2d_plot(name1, name2)
            filenames.append(filename)
        return filenames


class TestPlots(Plots):
    def run(self):
        ini=self.source.ini
        dirname = ini.get("test", "save_dir")
        output_dir = self.options.get("outdir", "png")
        prefix=self.options.get("prefix","")
        ftype=self.options.get("file_type", "png")
        filenames = []
        for cls in cosmology_theory_plots.plot_list:
            try:
                p=cls(dirname, output_dir, prefix, ftype, figure=None)
                filename=p.filename
                fig = self.figure(filename)
                p.figure=fig
                p.plot()
                filenames.append(filename)
            except IOError as err:
                print err
        return filenames

class MultinestPlots(Plots):
    pass
