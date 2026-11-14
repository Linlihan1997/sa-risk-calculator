# Redraw Figure 2 (LASSO path, LASSO CV, Boruta) with one serif font throughout
suppressPackageStartupMessages({ library(glmnet); library(Boruta); library(ggplot2); library(ggridges) })
FONT <- "Liberation Serif"            # Times New Roman–compatible metrics
root <- Sys.getenv("YRBS_SA_ROOT", ".")
set.seed(2026)
d <- read.csv(file.path(root, "data", "derived", "train_70_imputed.csv"), fileEncoding = "UTF-8-BOM")
vars <- c("age","grade","female","raceeth","sexual_minority","bmi","sad_hopeless","plan","sleep_hours",
          "nicotine_status","alcohol_status","marijuana_status","other_drug_any","early_onset_any",
          "bullying_count","school_victim_any","fighting_any","weapon_any","sexual_dating_violence_any",
          "sexual_behavior","fv_none_count","no_breakfast","drank_soda","pa_5days","sports_pe_any",
          "concussion","dentist","hiv_std_test_any")
lab <- c(age="Age", grade="Grade", female="Female sex", raceeth="Race/ethnicity", sexual_minority="Sexual minority",
         bmi="BMI", sad_hopeless="Persistent sadness/hopelessness", plan="Suicide plan", sleep_hours="Sleep hours",
         nicotine_status="Tobacco/nicotine use", alcohol_status="Alcohol use", marijuana_status="Marijuana use",
         other_drug_any="Lifetime illicit drug use or prescription opioid misuse", early_onset_any="Substance use before 13",
         bullying_count="Bullying victimization", school_victim_any="School violence/unsafe",
         fighting_any="Physical fighting", weapon_any="Weapon carrying",
         sexual_dating_violence_any="Sexual/dating violence", sexual_behavior="Sexual behavior",
         fv_none_count="Fruit/vegetable categories not eaten", no_breakfast="No breakfast",
         drank_soda="Soda consumption", pa_5days="Physically active on 5+ days/week", sports_pe_any="Sports team or PE",
         concussion="Sports concussion", dentist="Dental visit", hiv_std_test_any="HIV/STD testing")
d$raceeth <- relevel(factor(d$raceeth), ref = "White")
for (v in c("nicotine_status","alcohol_status","marijuana_status","sexual_behavior")) d[[v]] <- factor(d[[v]], levels = 0:2)
X <- model.matrix(~ ., data = d[, vars])[, -1]
foldid <- sample(rep(1:10, length.out = nrow(X)))          # identical to the original run (same seed and order)
cvfit <- cv.glmnet(X, d$sa, family = "binomial", alpha = 1, nfolds = 10, foldid = foldid, type.measure = "deviance")
cat(sprintf("lambda.min=%.5f lambda.1se=%.5f\n", cvfit$lambda.min, cvfit$lambda.1se))

draw_ab <- function() {
  par(mfrow = c(2, 1), mar = c(4.8, 5, 4.2, 1.5), family = FONT, cex.lab = 1.35, cex.axis = 1.15)
  plot(cvfit$glmnet.fit, xvar = "lambda", label = FALSE, lwd = 1.2, xlab = "Log(\u03bb)", ylab = "Coefficients")
  abline(v = log(c(cvfit$lambda.min, cvfit$lambda.1se)), lty = 2)
  mtext("A", side = 3, line = 2.2, adj = -0.12, cex = 2.2, font = 2)
  plot(cvfit, xlab = "Log(\u03bb)", ylab = "Binomial Deviance")
  mtext("B", side = 3, line = 2.2, adj = -0.12, cex = 2.2, font = 2)
}
png(file.path(root, "results", "fig2_AB.png"), width = 7, height = 10, units = "in", res = 300, type = "cairo"); draw_ab(); dev.off()
cairo_pdf(file.path(root, "results", "fig2_AB.pdf"), width = 7, height = 10, family = FONT); draw_ab(); dev.off()

bor <- readRDS(file.path(root, "results", "feature_selection", "train_boruta.rds"))
st <- attStats(bor)
ih <- as.data.frame(bor$ImpHistory)[, vars]
long <- data.frame(variable = rep(vars, each = nrow(ih)), imp = unlist(ih, use.names = FALSE))
long <- long[is.finite(long$imp), ]
long$decision <- factor(as.character(st[long$variable, "decision"]), levels = c("Confirmed", "Rejected", "Tentative"))
ord <- names(sort(tapply(long$imp, long$variable, median)))
long$label <- factor(lab[long$variable], levels = lab[ord])
pC <- ggplot(long, aes(x = imp, y = label, fill = decision)) +
  geom_density_ridges(scale = 2.2, rel_min_height = 0.01, alpha = 0.9, colour = "black", linewidth = 0.3) +
  scale_fill_manual(values = c(Confirmed = "#3EC1C8", Rejected = "#E8605F", Tentative = "#F2C230"), drop = FALSE) +
  labs(x = "Importance (Z-score)", y = "Features", fill = "Decision", tag = "C") +
  theme_bw(base_size = 16, base_family = FONT) +
  theme(plot.tag = element_text(size = 26, face = "bold", family = FONT),
        axis.text = element_text(colour = "black", family = FONT), text = element_text(family = FONT),
        legend.position = "bottom", legend.title = element_text(face = "bold"))
ggsave(file.path(root, "results", "fig2_C.png"), pC, width = 9, height = 10, dpi = 300, type = "cairo")
ggsave(file.path(root, "results", "fig2_C.pdf"), pC, width = 9, height = 10, device = cairo_pdf)
